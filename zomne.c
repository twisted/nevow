
#include <sys/types.h>
#include <sys/param.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/unistd.h>
#include <sys/stat.h>
#include <stdio.h>
#include <dirent.h>
#include <errno.h>

extern char **environ;
const char* STDIN_FN_KEY = "STDIN_FILENAME=";

#warning "zomne.c is deprecated, don't use it."

int copyfds(int ind, int outd) {
  size_t read, written;
  char scratch[4096];
  FILE* in;
  FILE* out;
  int rv = 0;

  in = fdopen(ind, "r"); out = fdopen(outd, "w");
  for (;;) {
    read = fread(scratch, 1, sizeof scratch, in);
    if (read != sizeof scratch && ferror(in))
      goto cleanup;
    if (read == 0)
      break;
    written = fwrite(scratch, 1, read, out);
    if (written != read)
      goto cleanup; }

  rv = 1;

 cleanup:
  fclose(in);
  fclose(out);
  return rv; }


int err_die(char* argv) {
  printf("Content-Type: text/plain\r\n\r\n");
  printf(argv);
  printf("\r\n");
  return 1; }


int get_config(char* whatdir, char* whatfile, char* whatbuffer, int die) {
  char scratch[MAXPATHLEN+1024];
  FILE *handle;
  struct stat st;

  if (whatdir)
    chdir(whatdir);

  handle = fopen(whatfile, "r");
  if (!handle) {
    if (die) {
        sprintf(scratch, "Could not open file '%s' in directory '%s'. errno = %d.\n", whatfile, whatdir, errno);
        return err_die(scratch); }
    return 1; }

  fread(whatbuffer, 1, MAXPATHLEN, handle);
  fclose(handle);

  return 0; }


int start_twistd(char* basedir) {
  char scratch[MAXPATHLEN];
  char env_value[MAXPATHLEN];
  char tacfile[MAXPATHLEN];
  FILE* handle;
  DIR* environ_dir;
  struct dirent *fl;
  int err, startup_complete_sock, startup_complete_accepted;
  struct sockaddr_un server;


  sprintf(tacfile, "%s/%s", basedir, "zomne.tac");
  handle = fopen(tacfile, "r");
  if (!handle) return err_die("Could not open tacfile zomne.tac");
  fclose(handle);

  // We have an "environment" directory, which is full of files
  // which are named with environment keys and who contain environment values.
  // Iterate all the files, and set keys in the environment so the child sees
  // them.
  if (!((environ_dir = opendir("zomne_environ")) == NULL)) {
    chdir("zomne_environ");
    while ((fl = readdir(environ_dir)) != NULL) {
      if (err = get_config("", fl->d_name, env_value, 1)) return err;
      if (setenv(fl->d_name, env_value, 1))
	return err_die("Unknown error setting environment"); } }

  chdir(basedir);

  startup_complete_sock = socket(AF_UNIX, SOCK_STREAM, 0);
  if (startup_complete_sock < 0) return err_die("Error creating socket for startup completion notification");
  server.sun_family = AF_UNIX;
  strcpy(server.sun_path, "zomne_startup_complete.socket");
  if (bind(startup_complete_sock, (struct sockaddr *) &server, sizeof(struct sockaddr_un)))
    return err_die("Error binding zomne_startup_complete.socket");
  listen(startup_complete_sock, 1);

  sprintf(scratch, "twistd -oy %s", tacfile);
  system(scratch);

  // This blocks until the twisted process calls connectUNIX('zomne_startup_complete.socket')
  startup_complete_accepted = accept(startup_complete_sock, 0, 0);
  close(startup_complete_accepted);
  close(startup_complete_sock);
  unlink("zomne_startup_complete.socket");
  return 0; }


int main(int argc, char* argv[]) {
  struct sockaddr_un addr;
  int s, tempfd, bytesread, err, pid;
  char scratch[MAXPATHLEN];
  char basedir[MAXPATHLEN];
  char stdin_temp[MAXPATHLEN];
  char **enviter = environ;
  FILE* config_file;
  char *program_name;

  program_name = (char*)getenv("SCRIPT_NAME");
  if (!program_name)
    // If argv[0] contains any slashes, we just want the bit after the slash
    // aka argv[0].split('/')[-1]
    program_name = argv[0];

  while (*program_name++); // Move the pointer to the end of the string
  while (*(program_name-1) != '/')
    program_name--; // Move the pointer back to the slash
  sprintf(scratch, ".%s.dir", program_name);
  if (err = get_config("", scratch, basedir, 1)) return err;
  chdir(basedir);

  if (get_config(basedir, "twistd.pid", scratch, 0)) {
    // No pidfile, got to start twisted
    if (err = start_twistd(basedir)) return err;
  } else {
    // TODO Send a signal to the pid to see if it is alive.
    // Got an error?
    // It is dead, start it up
  }

  s = socket(AF_UNIX, SOCK_STREAM, 0);
  if (s < 0) {
    return err_die("Error creating socket"); }

  sprintf(addr.sun_path, "%s%s", basedir, "zomne.socket");
  addr.sun_family = AF_UNIX;

  if (connect(s, (struct sockaddr *)&addr, sizeof(struct sockaddr_un))) {
    return err_die("Couldn't connect to server");
  } else {
    while (*enviter != 0) {
      sprintf(scratch, "%u:", strlen(*enviter));
      send(s, scratch, strlen(scratch), 0);
      send(s, *enviter, strlen(*enviter), 0);
      send(s, ",", strlen(","), 0);
      enviter += 1; }

    getcwd(scratch, MAXPATHLEN);
    sprintf(stdin_temp, "%s/%s", scratch, "tmp.zomneXXXXXX");
    tempfd = mkstemp(stdin_temp);
    copyfds(STDIN_FILENO, tempfd);
    sprintf(scratch, "%u:%s%s",
	    strlen(STDIN_FN_KEY) + strlen(stdin_temp),
	    STDIN_FN_KEY,
	    stdin_temp);
    send(s, scratch, strlen(scratch), 0);
    while (bytesread = recv(s, scratch, 1024, 0)) {
      fwrite(scratch, 1, bytesread, stdout); }

    unlink(stdin_temp); }

  close(s); }


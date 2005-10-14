CREATE TABLE todos (
    id serial primary key,
    description varchar(100) not null,
    done int not null
)
Setting Up the Tutorial Environment and Running Tutorial Source Code
====================================================================

To run this tutorial, you need to have nevow available to python and
you'll need the files in the doc/howto tree. You don't even have to
install nevow; the examples will run within the source tree.

Combinator: The Divmod Way
~~~~~~~~~~~~~~~~~~~~~~~~~~

Using SVN with
`Combinator <http://divmod.org/trac/wiki/DivmodCombinator>`__ is the
best way to try out the example code in-place (and hop between other SVN
branches in the future). This is how we develop and test our
applications at Divmod. If you have a system installation of Twisted
that you don't want to update or interfere with, you can use this method
without installing anything.

1. Create a projects directory or change to some other test directory of
   your choice::

   $ mkdir ~/Projects
   $ cd ~/Projects

2. If you don't have the `twisted
   library <http://twistedmatrix.com/trac/>`__, check it out now::

   $ svn co svn://svn.twistedmatrix.com/svn/Twisted/trunk Twisted/trunk

3. Then get Combinator and Nevow (and the rest of Divmod). See the
   `Combinator
   Tutorial <http://divmod.org/trac/wiki/CombinatorTutorial>`__ for more
   about these special checkout paths.::

   $ svn co http://divmod.org/svn/Divmod/trunk Divmod/trunk

4. Set up the Combinator environment in this shell. You'll need this
   step in any future test shells since it adjusts PATH and PYTHONPATH::

   $ eval ``python Divmod/trunk/Combinator/environment.py``
   $ # (some "link:" lines are normal)

5. Register both the Twisted and Divmod (and thus Nevow+Athena)
   codebases with Combinator::

   $ chbranch Twisted trunk
   $ chbranch Divmod trunk

6. You can check to see if your environment is ready to go by running
   the tutorial tests (from any directory, after executing the previous
   command)::

   $ trial nevow.test.test\_howtolistings

If they all pass, you're ready to begin the tutorial.

Standard distutils Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you don't want to manage branches and environments with Combinator,
you can install our code in the standard ``site-packages`` directory.
You'll still need the source tree so you can use the files in doc/howto.

For those that would prefer the old way, here's how you do it:

1. Create a projects directory::

   $ mkdir ~/Projects
   $ cd ~/Projects

2. Checkout and install the latest Twisted::

   $ svn co svn://svn.twistedmatrix.com/svn/Twisted/trunk Twisted
   $ cd Twisted
   $ sudo python setup.py install
   $ cd ../

3. Checkout and install Nevow::

   $ svn co http://divmod.org/svn/Divmod/trunk/Nevow Nevow
   $ cd Nevow
   $ sudo python setup.py install
   $ cd ../



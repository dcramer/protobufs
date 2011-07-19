#! /usr/bin/python
#
# See README for usage instructions.

# We must use setuptools, not distutils, because we need to use the
# namespace_packages option for the "google" package.
try:
    from setuptools import setup, Extension, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, Extension, find_packages

from distutils.spawn import find_executable
import sys
import os
import subprocess

maintainer_email = "protobuf@googlegroups.com"

root = os.path.dirname(__file__)

# Find the Protocol Compiler.
exec_paths = [
    os.path.join(root, 'src', 'protoc'),
    os.path.join(root, 'src', 'protoc.exe'),
    os.path.join(root, 'vsprojects', 'Debug', 'protoc.exe'),
    os.path.join(root, 'vsprojects', 'Release', 'protoc.exe'),
    find_executable('protoc'),
]
protoc = None
while exec_paths:
    path = exec_paths.pop()
    if os.path.exists(path):
        protoc = path
        break

def generate_proto(source):
  """Invokes the Protocol Compiler to generate a _pb2.py from the given
  .proto file.  Does nothing if the output already exists and is newer than
  the input."""

  output = source.replace(".proto", "_pb2.py").replace("../src/", "")

  if not os.path.exists(source):
    print "Can't find required file: " + source
    sys.exit(-1)

  if (not os.path.exists(output) or
      (os.path.exists(source) and
       os.path.getmtime(source) > os.path.getmtime(output))):
    print "Generating %s..." % output

    if protoc == None:
      sys.stderr.write(
          "protoc is not installed nor found in src.  Please compile it "
          "or install the binary package.\n")
      sys.exit(-1)

    protoc_command = [ protoc, "-Isrc", "-I.", "--python_out=python", source ]
    if subprocess.call(protoc_command) != 0:
      sys.exit(-1)

def MakeTestSuite():
  # This is apparently needed on some systems to make sure that the tests
  # work even if a previous version is already installed.
  if 'google' in sys.modules:
    del sys.modules['google']

  generate_proto(os.path.join(root, 'src', 'google', 'protobuf', 'unittest.proto'))
  generate_proto(os.path.join(root, 'src', 'google', 'protobuf', 'unittest_custom_options.proto'))
  generate_proto(os.path.join(root, 'src', 'google', 'protobuf', 'unittest_import.proto'))
  generate_proto(os.path.join(root, 'src', 'google', 'protobuf', 'unittest_mset.proto'))
  generate_proto(os.path.join(root, 'src', 'google', 'protobuf', 'unittest_no_generic_services.proto'))
  generate_proto(os.path.join(root, 'python', 'google', 'protobuf', 'internal', 'more_extensions.proto'))
  generate_proto(os.path.join(root, 'python', 'google', 'protobuf', 'internal', 'more_messages.proto'))

  import unittest
  import google.protobuf.internal.generator_test     as generator_test
  import google.protobuf.internal.descriptor_test    as descriptor_test
  import google.protobuf.internal.reflection_test    as reflection_test
  import google.protobuf.internal.service_reflection_test \
    as service_reflection_test
  import google.protobuf.internal.text_format_test   as text_format_test
  import google.protobuf.internal.wire_format_test   as wire_format_test

  loader = unittest.defaultTestLoader
  suite = unittest.TestSuite()
  for test in [ generator_test,
                descriptor_test,
                reflection_test,
                service_reflection_test,
                text_format_test,
                wire_format_test ]:
    suite.addTest(loader.loadTestsFromModule(test))

  return suite

if __name__ == '__main__':
  # TODO(kenton):  Integrate this into setuptools somehow?
  if len(sys.argv) >= 2 and sys.argv[1] == "clean":
    # Delete generated _pb2.py files and .pyc files in the code tree.
    for (dirpath, dirnames, filenames) in os.walk("."):
      for filename in filenames:
        filepath = os.path.join(dirpath, filename)
        if filepath.endswith("_pb2.py") or filepath.endswith(".pyc") or \
          filepath.endswith(".so") or filepath.endswith(".o"):
          os.remove(filepath)
  else:
    # Generate necessary .proto file if it doesn't exist.
    # TODO(kenton):  Maybe we should hook this into a distutils command?
    for path in [os.path.join(root, 'src', 'google', 'protobuf', 'descriptor.proto'),
                 os.path.join(root, 'src', 'google', 'protobuf', 'compiler', 'plugin.proto')]:
        if os.path.exists(path):
            generate_proto(path)

  ext_module_list = []

  # C++ implementation extension
  if os.getenv("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python") == "cpp":
    print "Using EXPERIMENTAL C++ Implmenetation."
    ext_module_list.append(Extension(
        "google.protobuf.internal._net_proto2___python",
        [ os.path.join(root, 'python', 'google', 'protobuf', 'pyext', 'python_descriptor.cc'),
          os.path.join(root, 'python', 'google', 'protobuf', 'pyext', 'python_protobuf.cc'),
          os.path.join(root, 'python', 'google', 'protobuf', 'pyext', 'python-proto2.cc') ],
        include_dirs = [ root ],
        libraries = [ "protobuf" ]))

  setup(name = 'protobuf',
        version = '2.4.1',
        package_dir = { 'google': 'python/google' },
        packages = find_packages('python'),
        package_data = {
            '': ['*.cc', '*.h', '*.proto'],
            'google.protobuf': ['pyext/*'],
        },
        namespace_packages = [ 'google' ],
        test_suite = 'setup.MakeTestSuite',
        ext_modules = ext_module_list,
        url = 'http://code.google.com/p/protobuf/',
        maintainer = maintainer_email,
        maintainer_email = 'protobuf@googlegroups.com',
        license = 'New BSD License',
        description = 'Protocol Buffers',
        long_description = open(os.path.join(root, 'README.txt')).read(),
        zip_safe = False)
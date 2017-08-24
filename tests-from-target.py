#!/usr/bin/python

# Have you ever been annoyed by having to manually harvest test class names so
# that you can run a comprehensive set of tests from a Chromium subcomponent?
# Yes, well, me too! And here's the solution for it.
#
# This script generates a Google Test formatted filter string using all C++ test
# classes it can find given an output dir and one or more GN targets. For
# instance this call:
#
# $ tests-from-target.py out_linux/Debug components/offline_pages/core/background:unit_tests
#
# Generates this output as of today:
#
# AddRequestTaskTest.*:ChangeRequestsStateTaskTest.*:CleanupTaskTest.*:
# GetRequestsTaskTest.*:InitializeStoreTaskTest.*:MarkAttemptAbortedTaskTest.*:
# MarkAttemptCompletedTaskTest.*:MarkAttemptStartedTaskTest.*:
# PickRequestTaskTest.*:ReconcileTaskTest.*:RemoveRequestsTaskTest.*:
# RequestCoordinatorEventLoggerTest.*:RequestCoordinatorTest.*:
# RequestQueueStoreSQLTest.*:RequestQueueTest.*:SavePageRequestTest.*
#
# The most common usage case will be to use your shell's command substitution so
# that the script populates the filter argument of your test execution call.
# For Bash it would be something like this (if you are cool and use cr! ;):
#
# cr run components_unittests --gtest_filter=$(tests-from-target.py <OUT_DIR> <GN_TEST_TARGET>)
#

import sys
import re
import os.path
import subprocess

def eprint(text):
  print >> sys.stderr, text

def GetGnSourcesFor(output_dir, gn_target):
  command = ["gn", "desc", output_dir, gn_target, "sources"]
  try:
    output = subprocess.check_output(command, shell=False)
  except subprocess.CalledProcessError as e:
    eprint("GN call failed with error code %s for command: %s"
           % (e.returncode, " ".join(command)))
    exit(p.returncode)
  gn_sources = output.splitlines()
  return gn_sources

def GetGnSourcesForAllTargets(output_dir, gn_targets):
  all_gn_sources = set()
  for gn_target in gn_targets:
    all_gn_sources.update(GetGnSourcesFor(output_dir, gn_target))
  return all_gn_sources

def ParseTestClasses(filename):
  with open(filename) as gtest_file:
    contents = gtest_file.read()
  test_class_name_regex = re.compile(r"\n(?:TEST|TEST_F)\(\s*(\w+)\s*,[^\)]+\)")
  test_classes = set()
  for match in test_class_name_regex.finditer(contents):
    test_classes.add(match.group(1))
  return test_classes

def ClassNamesFromGnSources(gn_sources):
  all_test_classes = set()
  for source_file in gn_sources:
    actual_file_name = source_file[2:]
    if os.path.isfile(actual_file_name):
      all_test_classes |= ParseTestClasses(actual_file_name)
    else:
      eprint("Couldn't find file from source: %s" % (source_file,))
  return all_test_classes

def BuildGoogleTestFilterString(test_class_names):
  filters = []
  for class_name in test_class_names:
    filters.append(class_name + ".*")
  filters.sort()
  return ":".join(filters)

if __name__ == "__main__":
  if len(sys.argv) < 3:
    command_only = os.path.basename(sys.argv[0])
    eprint("%s: prints a Google Test filter string containing all tests from "
           "GN targets' sources." % (command_only,))
    eprint("")
    eprint("Usage: %s <output_dir> <gn_target_1> <gn_target_2> ..."
           % (command_only,))
    exit(1)
  gn_sources = GetGnSourcesForAllTargets(sys.argv[1], sys.argv[2:])
  test_class_names = ClassNamesFromGnSources(gn_sources)
  print BuildGoogleTestFilterString(test_class_names)

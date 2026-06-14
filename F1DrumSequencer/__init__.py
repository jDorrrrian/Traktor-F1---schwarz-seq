# emacs-mode: -*- python-*-

from __future__ import absolute_import, print_function, unicode_literals

from .F1DrumSequencer import F1DrumSequencer


def create_instance(c_instance):
    return F1DrumSequencer(c_instance)

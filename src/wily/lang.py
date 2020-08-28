"""Language/i18n support for the CLI."""
# -*- coding: UTF-8 -*-

import gettext
import os

localedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'locales')
trans = gettext.translation('messages', localedir=localedir, fallback=True)
trans.install()
_ = trans.gettext
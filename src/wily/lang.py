# -*- coding: UTF-8 -*-

import gettext

trans = gettext.translation('messages', localedir='locales', languages=['en', 'en_AU', 'ja'], fallback='en')
trans.install()
_ = trans.gettext
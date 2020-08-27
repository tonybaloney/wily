build:
	flit build

install:
	flit install

extract_messages:
	xgettext src/wily/*.py -o src/wily/locales/messages.pot
	msgmerge src/wily/locales/ja/LC_MESSAGES/messages.po -U src/wily/locales/messages.pot

compile_messages:
	msgfmt src/wily/locales/ja/LC_MESSAGES/messages.po -o - > src/wily/locales/ja/LC_MESSAGES/messages.mo
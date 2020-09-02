build:
	flit build

install:
	flit install

extract_messages:
	find src/wily -iname "*.py" | xargs xgettext -o src/wily/locales/messages.pot
	find src/wily/locales -name \*.po -execdir msgmerge {} -U ../../../../../src/wily/locales/messages.pot \;

compile_messages:
	find src/wily/locales -name \*.po -execdir msgfmt {} -o messages.mo \;

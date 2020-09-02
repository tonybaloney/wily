"""
A Python application for tracking, reporting on timing and complexity in tests and applications.

           B        BB*
         BBBB      BBB
       BBBBBB%$%*SBBB&
      BBBBS&@$@$SBBBB
     BBS@$$$$@@$#BBB. .
    BB&$$@@@@@@$$@#! !..
    B&$*$@@@*.@@@$$@&&@&$             BB
    %$$!$@$@$$@@@@@@@@@$$B       SBBBBS###B
    %$@@$$$$@@$$$@&$@@@$$    SBBBBBBBBSSSSSB
     %$@#BBBBBBS&&@@@@@$$$%#BBBBBBBBBBBBBBB
  *@BBBBBBBBBBBBS@$@@@@@@@%SBBBBBBBBBBBBBB
@$$@BBBBBBBBBBB#@$@@@@@@@@$#BBBBBBBBBB                  BBBBBBBBBBB    BBB    BBBBBBBBBBBB   BBBBBBB
@$$$SBBBBSSS&!  *@@@@@@@@@$$#BBBBB#                     BBBBBBBBBBB    BBB    BBBBBBBBBBBB   BBBBBBB
@$@$$@&&$@&%S   $@@@@@@@@@@@$$#                            BBBBBB     BBBBB      BBB  BBBB     BBBBB
@$$$$$$$$&BBB. $#&&@@@@@@@@@$                               BBBBB    BBBBBBB    BBB     BB     BBBBB BBB   BBB  BB  BB
  %%$$@@$$@@*!@@*!*$@@@@@$$*                                 BBBBB   BBBBBBB    BBB BBBBBB     BBBBB BBBBBBBBB  BBBBBBB
     $$$$$$$@&*     .$@@@$$                                  BBBBB  BBB BBBBB  BBB  BBBBBB     BBBBB   BBBBB     BBBB
         %$$@@        $@@$$                                   BBBBB BBB BBBBB  BBB    BBBB     BBBBB    BBBBB    BBB
           $$@*        @@$$                                   BBBBB BB   BBBBBBBB     BBBB     BBBBB     BBBBB  BBB
            %@$        %@@$%                                   BBBBBBB    BBBBBB      BBBB     BBBBB      BBBBBBBB
             @!        %@@$$@$$$$$$$$                           BBBBB     BBBBBB      BBBB     BBBBB       BBBBBB   BBB
            $@!       !@@@@@@@@@@@@@@$$$$$$                     BBBBB      BBBB     BBBBBBBB BBBBBBBBB      BBBBB  BBBBB
           $$@@*.   !$&@@@@@@@@@@@@@@@@@@@@@@S                   BBB        BBB     BBBBBBBB BBBBBBBBB      BBBB   BBBBB
           $$@@@@@@@&@@@@@@@@@@@@@@@@@@&&&&@!!$@                                                           BBBB
         *$$@@@@@@@@@@@@@@@@@@@@@@@@@@@$ .*@!  %                                                          BBBB
        @$$@@@@@@@$*@@@@@@@@$$$@@@@@@@&&%   .      .                                                  BB BBBB
        %$@@$$@@@%   $@@@$$$$$$$@@@@@$*%@@*                                                          BBBBBBB
        $$$$$@@$      $@@#BBBBBB@@@&&@%!.........                                                    BBBBBB
        *&SBBBBBB       $BBBBBBB#@&@$$$%%*!........
         BBBBBBBB*       #BBBBBBB*
          BBBBBBBB        BBBBBBBB
      %$%%BBBBBBS%$$$$$$$$%&BBBBBBS@$$$$$%%$$$$$$%$$$&B*%
      %%$%$&&S#&$$@@@@@@@@@$$@&&&@$@@@@@@@@@@@@@@@@$$%%$$
               .%%$$$$%%%$%%%%***%%%%%$%%$$$$$%%$%*&
"""
import tempfile
import colorlog
import logging
import datetime

__version__ = "1.19.0"

_, WILY_LOG_NAME = tempfile.mkstemp(suffix="wily_log")

_handler = colorlog.StreamHandler()
_handler.setFormatter(colorlog.ColoredFormatter("%(log_color)s%(message)s"))

_filehandler = logging.FileHandler(WILY_LOG_NAME, mode="w+")
_filehandler.setLevel(logging.DEBUG)

logger = colorlog.getLogger(__name__)
logger.addHandler(_handler)
logger.addHandler(_filehandler)

""" Max number of characters of the Git commit to print """
MAX_MESSAGE_WIDTH = 50


def format_date(timestamp):
    """Reusable timestamp -> date."""
    return datetime.date.fromtimestamp(timestamp).isoformat()


def format_datetime(timestamp):
    """Reusable timestamp -> datetime."""
    return datetime.datetime.fromtimestamp(timestamp).isoformat()


def format_revision(sha):
    """Return a shorter git sha."""
    return sha[:7]

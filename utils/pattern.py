# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import re

"""
This package includes a list about search patterns
which the Autoseed only accept torrent's name match with.
NOTICE:
1.Every pattern should includes at least below groups, even it's empty.
  groups list:  `full_name` `search_name` `episode` `group` `filetype`
2.Every pattern should use re.compile() to compile
  a regular expression pattern into a regular expression object.
"""

# Search_pattern
pattern_group = [
    # Series (Which name match with 0day Source
    # see https://scenerules.org/t.html?id=tvx2642k16.nfo 16.4)
    re.compile(
        "\\.?(?P<full_name>(?P<search_name>[\\w\\-. ]+?)[. ]"
        "(?P<episode>([Ss]\\d+)?[Ee][Pp]?\\d+(-[Ee]?[Pp]?\\d+)?|[Ss]\\d+|Complete).+?"
        "(HDTV|WEB-DL|HDTVrip).+?(-(?P<group>.+?))?)"
        "(\\.(?P<filetype>\\w+)$|$)"
    ),
    # Anime - One_piece(Skytree)
    re.compile(
        "(?P<full_name>\\[(?P<group>Skytree)]\\[海贼王]"
        "\\[(?P<search_name>One_Piece)]"
        "\\[(?P<episode>\\d+)]\\[GB_JP]\\[X264_AAC]"
        "\\[720P]\\[CRRIP]\\[天空树双语字幕组])"
        "(\\.(?P<filetype>mp4)$|$)"
    ),
    # Anime - Group: 八重樱字幕组
    re.compile(
        "(?P<full_name>\\[(?P<group>八重[樱櫻]字幕[组組])]"
        "\\[.+?]\\[(?P<search_name>[^\\[\\]]+?)]"
        "\\[?(?P<episode>\\d+(\\.?\\d+|-\\d+|[ _]?[Vv]2)?)]?.+?)"
        "(\\.(?P<filetype>\\w+)$|$)"
    ),
    # Anime - Foreign Group or group list Kamigami, LoliHouse
    re.compile(
        "(?P<full_name>\\[(?P<group>[^\\[\\]]+?)] (?P<search_name>.+) - "
        "(?P<episode>\\d+(\\.?\\d+|-\\d+|[ _]?[Vv]2)?) \\[.+?[Pp].+?])"
        "(\\.(?P<filetype>\\w+)$|$)"
    ),
    # Anime - Nekomoe kissaten WebRip
    re.compile(
        "(?P<full_name>\\[(?P<group>[^\\[\\]]+?)] (?P<search_name>.+) "
        "(?P<episode>\\d+(\\.?\\d+|-\\d+|[ _]?[Vv]2)?) \\[.+?[Pp].+?])"
        "(\\.(?P<filetype>\\w+)$|$)"
    ),
    # Anime - YUI-7
    re.compile(
        "(?P<full_name>\\[(?P<group>[^\\[\\]]+?)]\\s"
        "\\[(?P<search_name>[^\\[\\]]+)]\\s?"
        "\\[?(?P<episode>\\d+(\\.?\\d+|-\\d+|[ _]?[Vv]2)?)]?.+?)"
        "(\\.(?P<filetype>\\w+)$|$)"
    ),
    # Anime - Normal Pattern
    re.compile(
        "(?P<full_name>\\[(?P<group>[^\\[\\]]+?)]"
        "(?P<n_s>\\[)?(?P<search_name>[^\\[\\]]+)(?(n_s)])"
        "\\[?(?P<episode>\\d+(\\.?\\d+|-\\d+|[ _]?[Vv]2)?)]?.+?)"
        "(\\.(?P<filetype>\\w+)$|$)"
    ),
]

if __name__ == "__main__":
    import requests

    test_txt_url = (
        "https://gist.github.com/Rhilip/34ad82070d71bb3fa75f293d24101588"
        "/raw/9%2520-%2520RegExp%2520Test%2520set.txt"
    )
    r = requests.get(test_txt_url)
    test_list = r.text.split("\n")
    # test_list = []
    # Test case for Nekomoe kissaten WebRip
    test_list.append(
        "[Nekomoe kissaten] Seijo no Maryoku wa Bannou Desu 12 "
        "[WebRip 1080p HEVC-10bit AAC ASSx2].mkv"
    )
    # Test cases for YUI-7
    test_list.extend(
        [
            "[UHA-WINGS&YUI-7] [Yami Shibai 9][01](CHS) (1080p) [CC2E4DC4]_x264.mp4",
            "[UHA-WINGS&YUI-7] [Yami Shibai 8] [13] [x264 1080p][CHS].mp4",
            "[YUI-7][Yami Shibai 6][12][GB][X264_AAC][720P].mp4",
        ]
    )
    for test_item in test_list:
        print("Test item: {}".format(test_item))
        for _id, ptn in enumerate(pattern_group):
            search = re.search(ptn, test_item)
            if search:
                print("Match pattern id: {} , {}".format(_id, search.groupdict()))
                break
        print()

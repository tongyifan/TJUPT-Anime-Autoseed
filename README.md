# TJUPT-Anime-Autoseed
一个普通的动漫发种:baby_chick:

人类的本质是复读机，重复造轮子真好玩。

## 动机
之前一直在用 [Rhilip/Pt-Autoseed](https://github.com/Rhilip/Pt-Autoseed) ，配置什么都算简单，但是比较令人苦恼的是每个番都要手动发布一个第一集，然后才能自动发布，不然就可能克隆到错误的种子。

## 改动
* 懒如我当然不想手动发布哪怕一个种子（x），因此打算通过增加一个**配置文件**的方式，令发种机自动从 [PT-Gen](https://ptgen.tju.pt) 中获取数据并发布。

* RSS部分不交由flexget处理，原因是如果加上动漫花园之类的RSS entry后，flexget速度就会变得特别特别慢，令同机的其他（刷流）任务较受影响。另外的一个打算是，在种子送入qbittorrent时记录匹配的entry，以便后面匹配配置文件。

## 配置说明
0. 配置Python环境，安装依赖
1. 复制 `config.sample.py` 至 `config.py` ，修改配置项
2. 按照 `instance/example.yaml` 的格式订阅番剧，并保存至 `instance/configs/{config_name}.yaml` ，注意首次运行时会自动更新配置文件来添加每个动漫的UUID，请不要在后面的改动中修改这个UUID
3. 运行 `rss.py` ，使用搜索模式初次更新番剧
   ```bash
   python rss.py -m search -c {config_name}
   ```
4. 添加crontab或计划任务，定期运行 `rss.py` 来通过rss模式加载新番
   ```bash
   python rss.py
   ```
5. 配置qBittorrent回调（Torrent完成时运行外部程序）：
   ```bash
   /path/to/python /path/to/autoseed.py %I
   ```

## 其他说明
1. 你可以为配置项手动添加info，如添加副标题（small_descr）的示例如下：
```yaml
items:
  无能力者娜娜:
    bangumi: http://bgm.tv/subject/302418
    info:
      small_descr: 无能力者娜娜
```
2. Windows可以使用在回调中使用 `pythonw.exe` 来实现无窗口化。如果出现配置文件解析问题时，请使用 `pythonw.exe -Xutf8 /path/to/autoseed.py`
3. 如果想要适配其他站点，请继承Autoseed类并自行实现 `format_torrent_info` 和 `post_to_site` ，当然你也可以在 `autoseed.py` 中直接修改（x

## TODO
* 对于已经出了很多集的动漫自动打包发布

## 参考项目
* [Rhilip/Pt-Autoseed](https://github.com/Rhilip/Pt-Autoseed) （utils/pattern.py 是直接从R酱那里复制过来的）
* [Rhilip/SJTU-Autoseed](https://github.com/Rhilip/SJTU-Autoseed)

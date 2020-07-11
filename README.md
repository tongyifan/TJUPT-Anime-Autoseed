# TJUPT-Anime-Autoseed
一个普通的动漫发种:baby_chick:

人类的本质是复读机，重复造轮子真好玩。

## 动机
之前一直在用 [Rhilip/Pt-Autoseed](https://github.com/Rhilip/Pt-Autoseed) ，配置什么都算简单，但是比较令人苦恼的是每个番都要手动发布一个第一集，然后才能自动发布，不然就可能克隆到错误的种子。

## 改动
* 懒如我当然不想手动发布哪怕一个种子（x），因此打算通过增加一个**配置文件**的方式，令发种机自动从 [PT-Gen](https://ptgen.tju.pt) 中获取数据并发布。

* RSS部分不交由flexget处理，原因是如果加上动漫花园之类的RSS entry后，flexget速度就会变得特别特别慢，令同机的其他（刷流）任务较受影响。另外的一个打算是，在种子送入qbittorrent时记录匹配的entry，以便后面匹配配置文件。

## TODO
* 优化cache流程
* 对于已经出了很多集的动漫自动打包发布

## 参考项目
* [Rhilip/Pt-Autoseed](https://github.com/Rhilip/Pt-Autoseed) （utils/pattern.py 是直接从R酱那里复制过来的）
* [Rhilip/SJTU-Autoseed](https://github.com/Rhilip/SJTU-Autoseed)

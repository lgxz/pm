# What
个人照片/视频文件管理工具。

目标：整理个人的所有历史照片/视频文件，方便存储和备份。

**注意**：
1. 在 MacOS 下使用 Python 3.7.3 开发和测试。
2. 依赖 exiftool 工具

# Why
为存储和备份目的，希望照片库能够满足：
1. 有且仅有需要存储的照片/视频文件
2. 目录结构简单清晰
3. 不改动照片/视频文件

现有的照片管理软件无法满足要求：
1. Apple Photos 不但修改文件，而且目录结构混乱，文件名也混乱
2. Lightroom CC 版像病毒一样，而且各种烦人的提示
3. Synology Photo Station 在照片库目录下创建大量文件，而且转换原始文件

# How
## 照片库格式
1. 为一个单独目录
2. 目录下，按年/月/日建立子目录结构，如 2019/07/05/
3. 照片/视频文件，按拍照日期存在对应的目录下。文件名为拍照时间，如 10305900，表示 10:30:59，00位两位数字序号
4. 管理信息存储在目录下的 .hash 文件里，无其它额外文件

## 工具描述
./bin/prepare.sh 负责预处理要导入的图片目录，输出包括文件路径，文件MD5，文件各种Exif时间的 CSV 文件，供 pm.py 处理。

./bin/pm 提供下述命令：
1. import: 处理 prepare.sh 输出的 CSV 文件，导入文件到图片库
2. sync: 同步图片库状态。即，保证图片库里的文件，和 .hash 文件一致
3. stat: 统计和显示图片库状态

pm 命令的通用参数如下：
1. --home: 图片库目录，默认为 "~/.photos"，可以为符号链接
2. --test: dryrun 模式，不修改
3. --verbose

## 文件导入
1. 执行 `./bin/prepare.sh <要导入的大量图片文件的绝对路径>` 生成 exif.csv 列表文件
2. 执行 `./bin/pm import exif.csv` 导入文件

## 备份
### 本地
同步最新的照片库(src) 到 USB/NAS 目录(dest)：
`rsync -av --progress --delete src/ dest`

### 云端
使用 restic 加密备份。把照片库目录直接添加到 restic 的 repo，实现增量加密备份。

### Google Photos
把照片库目录添加到 Google Sync 程序的备份目录。

# 赞助
如果这个项目对你有用，欢迎打赏：

<img src="https://user-images.githubusercontent.com/858592/60753727-af6fcb80-a009-11e9-9239-ee1a5b2c0c31.png" width="70%">



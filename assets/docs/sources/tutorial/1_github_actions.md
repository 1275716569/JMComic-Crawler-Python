# GitHub Actions使用教程


![tutorial](../images/github_actions_tutorial.jpg)

一共需要三步：

1. fork一份我的代码仓库。
2. 填写你需要下载的本子id。
3. 等待GitHub Actions下载完成，下载成品zip文件。

下面截图解析这三步的详细过程。

## 1. fork一份我的代码仓库

访问下面这个网址：

`https://github.com/hect0x7/JMComic-Crawler-Python/fork`

直接拉到页面最底部，如下所示：

（最新提示，下图的1可以不做，即直接点绿色的Create fork按钮）

![1](../images/1.png)

## 2. 填写你需要下载的本子id

在开始下面的步骤之前，你需要先启用你的repo的Actions，开启方式如下：
![6](../images/6.png)


### 2.1. 方式一（最新、简单、推荐）

访问下面这个网址：

`https://github.com/你的用户名/JMComic-Crawler-Python/actions/workflows/download_dispatch.yml`

按下图步骤进行操作：

![5](../images/5.png)

下载后的导出方式默认是「是 | 章节维度合并长图」：每个章节的图片按页序竖向拼接，生成一张 PNG 长图。
长图保存在 `long_img/` 目录中，文件名包含本子 ID、章节序号、章节 ID 和章节标题。
成功生成长图后会删除该章节的原始分页图片；不同宽度的图片会按比例缩放到该章节的最小页宽。

导出方式在表单中仍使用 `PDF_OPTION` 作为输入名，也可以选择「否」保留分页图片，或选择按本子、按章节合并 PDF。
`PDF_NAME_RULE` 仅用于 PDF 命名；`IMAGE_SUFFIX` 和 `IMAGE_QUALITY` 用于处理下载的分页图片，长图输出始终是 PNG。

`UPLOAD_NAME` 决定最终下载的 ZIP 名称，无需填写 `.zip` 后缀。已移除 `ZIP_NAME`，不再生成内部的 tar.gz 压缩包。

### 2.2. 方式二

访问下面这个网址：

`https://github.com/你的用户名/JMComic-Crawler-Python/edit/master/usage/workflow_download.py`

其实就是编辑 `usage/workflow_download.py`文件，任意分支皆可。

按下图步骤进行操作：

![2](../images/2.png)

看到上面的绿色框里的代码了吗？（位置可能有些变化）

上面有注释，把你要下载的本子的id填入，一行一个，id前面可以带`JM`。

填完点提交，会自动触发GitHub Actions下载这些本子。

## 3. 等待GitHub Actions下载完成，下载成品zip文件

来到Actions页面，选择最新的一次记录，等待它完成。

![3](../images/3.png)

完成以后，在页面最底部，点击下载你的成品即可。

默认下载结果的结构如下，解压一次即可查看各章长图：

```text
Click me to download.zip
└── long_img/
    ├── [JM123] 第1章-JM456-章节标题.png
    └── [JM123] 第2章-JM789-章节标题.png
```

两种下载工作流均使用当前仓库内的代码，不再运行时覆盖为上游脚本。
需要更新上游功能时，请先同步并检查自己的定制改动。

![4](../images/4.png)

如果你发现GitHub Actions显示❌，表明出现了问题，运行失败。

下面是问题的排查步骤：

1. 检查你在步骤2中填写是否有误。
2. 点进build，查看运行流程，找到`运行下载脚本`这个步骤，查看报错的具体信息
3. 来到我的项目仓库，点进Issue，先根据报错信息搜索Issue，如果能搜到类似问题，自行参考解决。
4. 如果还是不知道如何解决，提一个Issue，详细描述下你的问题。

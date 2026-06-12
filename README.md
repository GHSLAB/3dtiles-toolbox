# 3D Tiles 下载器

## 项目简介

3D Tiles 下载器是一个用于从指定URL下载3D Tiles数据的Python工具，支持交互式操作、URI列表保存和加载、多线程下载等功能。

## 功能特性

- ✅ 从URL提取3D Tiles的URI列表
- ✅ 支持保存URI列表到本地文件
- ✅ 支持从本地文件加载URI列表
- ✅ 多线程下载，提高下载速度
- ✅ 模拟浏览器请求头，提高下载成功率
- ✅ 简化的下载结果检查
- ✅ 交互式操作界面，易于使用

## 安装要求

- Python 3.7+
- 依赖库：
  - requests
  - tqdm

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本使用

直接运行脚本：

```bash
python main.py
```

### 操作流程

1. **选择操作模式**
   - 1. 从URL提取URI并下载
   - 2. 从本地文件加载URI并下载

2. **输入URL（模式1）**
   - 输入3D Tiles tileset.json的完整URL
   - 例如：http://example.com/tileset.json

3. **URI列表处理（模式1）**
   - 程序自动提取所有URI
   - 显示找到的URI数量
   - 询问是否保存URI列表到本地
   - 如果选择保存，输入保存路径

4. **下载确认**
   - 询问是否开始下载
   - 输入保存地址

5. **开始下载**
   - 显示下载进度
   - 下载完成后显示实际文件数量

## URI列表文件格式

保存的URI列表文件采用JSON格式，按照以下结构保存：

```json
{
  "tileset_uri": "http://example.com/tileset.json",
  "children_jsons": [
    "http://example.com/subtiles/subtileset.json",
    "http://example.com/subtiles/another_tileset.json"
  ],
  "resource_uris": [
    "http://example.com/tiles/tile1.b3dm",
    "http://example.com/tiles/tile2.b3dm",
    "http://example.com/tiles/tile3.pnts"
  ]
}
```

- `tileset_uri`: 主tileset.json的URL
- `children_jsons`: 子JSON文件的URL列表
- `resource_uris`: 资源文件的URL列表

## 代码结构

```
├── main.py              # 主程序文件
└── README.md           # 项目说明文档
```

### 核心函数

- `extract_all_uris_from_json`: 递归提取JSON数据中的所有URI
- `extract_uri_from_url`: 从URL提取所有URI，包括递归处理子JSON
- `download_3dtiles`: 多线程下载3D Tiles
- `download_uri`: 单个文件下载函数
- `save_uris_to_file`: 保存URI列表到本地文件
- `load_uris_from_file`: 从本地文件加载URI列表
- `validate_url`: 验证URL是否有效

## 注意事项

1. 确保输入的URL格式正确，以http或https开头
2. 保存URI列表时，建议使用.json扩展名
3. 下载大型3D Tiles数据集时，可能需要较长时间
4. 下载过程中请勿关闭终端窗口
5. 如遇到下载失败，可尝试重新运行程序

## 更新日志

### v0.1.0 (2025-12-29)

- 初始版本发布
- 支持从URL提取URI列表
- 支持多线程下载
- 支持保存和加载URI列表
- 支持浏览器请求头模拟
- 简化的下载结果检查
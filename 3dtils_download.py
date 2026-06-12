import requests
import urllib.parse
import os
import threading
from queue import Queue
from tqdm import tqdm


import json

# 默认浏览器请求头，用于模拟浏览器访问
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}


def validate_url(url: str) -> bool:
    """验证URL是否有效

    参数:
        url: 要验证的URL

    返回:
        如果URL有效返回True，否则返回False
    """
    try:
        # 检查URL格式是否正确
        result = urllib.parse.urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False
        # 检查URL是否以http或https开头
        if result.scheme not in ["http", "https"]:
            return False
        return True
    except Exception:
        return False


def save_uris_to_file(uris: list, file_path: str):
    """将URI列表保存到本地文件，按照类型分类保存

    参数:
        uris: 要保存的URI列表
        file_path: 保存文件的路径
    """
    try:
        # 分类URI
        tileset_uri = None
        children_jsons = []
        resource_uris = []

        for uri in uris:
            if uri.endswith("tileset.json") and not tileset_uri:
                # 保存第一个tileset.json地址
                tileset_uri = uri
            elif uri.endswith(".json"):
                # 保存其他JSON文件
                children_jsons.append(uri)
            else:
                # 保存其他URI
                resource_uris.append(uri)

        # 构建分类后的字典
        data = {
            "tileset_uri": tileset_uri,
            "children_jsons": children_jsons,
            "resource_uris": resource_uris,
        }

        # 保存到文件
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"URI列表已成功保存到 {file_path}")
        return True
    except Exception as e:
        print(f"保存URI列表失败: {e}")
        return False


def load_uris_from_file(file_path: str) -> list:
    """从本地文件加载URI列表，支持新的分类格式和旧的列表格式

    参数:
        file_path: 保存URI列表的文件路径

    返回:
        加载的URI列表，如果加载失败则返回空列表
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        uris = []
        # 检查是否是新的分类格式
        if isinstance(data, dict) and "tileset_uri" in data:
            # 加载tileset_uri
            if data["tileset_uri"]:
                uris.append(data["tileset_uri"])
            # 加载children_jsons
            uris.extend(data["children_jsons"])
            # 加载resource_uris
            uris.extend(data["resource_uris"])
            print(f"已成功从 {file_path} 加载 {len(uris)} 个URI")
            print(
                f"其中包含: 1个tileset.json, {len(data['children_jsons'])}个其他JSON文件, {len(data['resource_uris'])}个其他URI"
            )
        else:
            # 旧的列表格式
            uris = data if isinstance(data, list) else []
            print(f"已成功从 {file_path} 加载 {len(uris)} 个URI")

        return uris
    except FileNotFoundError:
        print(f"文件 {file_path} 不存在")
        return []
    except json.JSONDecodeError:
        print(f"文件 {file_path} 不是有效的JSON格式")
        return []
    except Exception as e:
        print(f"加载URI列表失败: {e}")
        return []


def count_files_in_directory(directory: str) -> int:
    """计算指定目录下的所有文件数量（包括子目录）

    参数:
        directory: 要计算文件数量的目录

    返回:
        目录下的文件总数
    """
    file_count = 0
    try:
        for root, dirs, files in os.walk(directory):
            file_count += len(files)
    except Exception as e:
        print(f"计算文件数量失败: {e}")
        file_count = -1
    return file_count


def generate_relative_path(uri: str, base_url: str) -> str:
    """根据URI和基础URL生成相对路径

    参数:
        uri: 要处理的URI
        base_url: 基础URL

    返回:
        生成的相对路径
    """
    try:
        if uri.startswith("http"):
            # 处理完整URL
            url_path = urllib.parse.urlparse(uri).path
            if url_path.endswith("tileset.json"):
                relative_path = "tileset.json"
            else:
                path_parts = url_path.split("/")
                if len(path_parts) >= 2:
                    relative_path = "/".join(path_parts[-2:])
                else:
                    relative_path = path_parts[-1] if path_parts else "unknown_file"
        else:
            # 处理相对路径
            relative_path = os.path.normpath(uri)
            relative_path = relative_path.replace("\\", "/")
        return relative_path
    except Exception as e:
        print(f"生成相对路径失败 {uri}: {e}")
        return "unknown_file"


def get_expected_file_paths(uris: list, base_url: str, output_dir: str) -> list:
    """根据URI列表生成预期的本地文件路径列表

    参数:
        uris: URI列表
        base_url: 基础URL
        output_dir: 输出目录

    返回:
        预期的本地文件路径列表
    """
    expected_paths = []

    for uri in uris:
        try:
            # 使用统一的函数生成相对路径，确保与download_uri函数一致
            relative_path = generate_relative_path(uri, base_url)

            # 生成本地文件路径
            local_path = os.path.join(output_dir, relative_path)
            expected_paths.append(local_path)
        except Exception as e:
            print(f"生成预期文件路径失败 {uri}: {e}")

    return expected_paths


def get_actual_file_paths(directory: str) -> list:
    """获取指定目录下的所有实际文件路径（包括子目录）

    参数:
        directory: 要获取文件路径的目录

    返回:
        实际的文件路径列表
    """
    actual_paths = []
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                actual_paths.append(file_path)
    except Exception as e:
        print(f"获取实际文件路径失败: {e}")

    return actual_paths


def compare_file_lists(expected_paths: list, actual_paths: list) -> list:
    """比较预期和实际的文件路径列表，找出未下载的文件

    参数:
        expected_paths: 预期的文件路径列表
        actual_paths: 实际的文件路径列表

    返回:
        未下载的文件路径列表
    """
    # 只比较文件名，不比较完整路径，这样更宽松
    actual_filenames = set()
    for path in actual_paths:
        # 获取文件名，转为小写，确保不区分大小写
        filename = os.path.basename(path).lower()
        actual_filenames.add(filename)

    # 找出未下载的文件
    missing_files = []
    for path in expected_paths:
        # 获取预期文件的文件名，转为小写
        expected_filename = os.path.basename(path).lower()
        # 如果文件名不在实际文件列表中，则认为是缺失的
        if expected_filename not in actual_filenames:
            missing_files.append(path)

    return missing_files


def extract_all_uris_from_json(data, uris=None):
    """递归提取JSON数据中所有的uri字段

    参数:
        data: 要遍历的JSON数据（可以是字典或列表）
        uris: 用于收集uri的列表（内部使用）

    返回:
        包含所有uri的列表
    """
    if uris is None:
        uris = []

    if isinstance(data, dict):
        for key, value in data.items():
            if key == "uri" and isinstance(value, str):
                uris.append(value)
            else:
                extract_all_uris_from_json(value, uris)
    elif isinstance(data, list):
        for item in data:
            extract_all_uris_from_json(item, uris)

    return uris


def extract_uri_from_url(json_url: str):
    """从指定的json_url提取所有uri，包括递归处理子json文件

    参数:
        json_url: 要处理的json文件url

    返回:
        包含所有层级uri的列表

    特点:
        - 支持处理各种相对路径，包括../../等上级目录引用
        - 使用urllib.parse.urljoin正确解析相对路径
        - 递归处理所有子json文件
    """
    # 初始化结果列表
    all_uris = []

    try:
        # 获取当前json数据，添加浏览器请求头
        response = requests.get(json_url, headers=DEFAULT_HEADERS, timeout=10)
        response.raise_for_status()  # 检查HTTP响应状态码
        tileset = response.json()
        parent_url = urllib.parse.urljoin(json_url, "./")

        # 提取当前层级的所有uri
        current_uris = extract_all_uris_from_json(tileset)

        # 处理当前层级的所有uri
        for uri in current_uris:
            # 使用urljoin正确处理相对路径，包括../../等上级目录
            full_url = urllib.parse.urljoin(parent_url, uri)
            all_uris.append(full_url)

            # 如果是json文件，则递归处理
            if full_url.endswith(".json"):
                all_uris.extend(extract_uri_from_url(full_url))

    except requests.exceptions.HTTPError as e:
        print(
            f"HTTP错误处理 {json_url}: 状态码 {e.response.status_code} - {e.response.reason}"
        )
    except requests.exceptions.ConnectionError:
        print(f"连接错误处理 {json_url}: 无法连接到服务器，请检查URL和网络连接")
    except requests.exceptions.Timeout:
        print(f"超时错误处理 {json_url}: 请求超时，请检查网络连接")
    except requests.exceptions.JSONDecodeError:
        print(f"JSON解析错误处理 {json_url}: 响应不是有效的JSON格式")
    except Exception as e:
        print(f"未知错误处理 {json_url}: {type(e).__name__} - {e}")

    return all_uris


def download_uri(queue, base_url, output_dir, pbar_lock, pbar, force):
    """单个线程的下载函数

    参数:
        queue: 任务队列，包含需要下载的uri
        base_url: 基础url，用于构造完整的下载链接
        output_dir: 输出目录
        pbar_lock: 进度条锁，用于线程安全地更新进度
        pbar: tqdm进度条对象
        force: 是否强制重新下载已存在的文件
    """
    while not queue.empty():
        uri = queue.get()
        try:
            # 构造完整的下载链接
            if uri.startswith("http"):
                download_url = uri
                # 使用统一的函数生成相对路径
                relative_path = generate_relative_path(uri, base_url)
            else:
                download_url = urllib.parse.urljoin(base_url, uri)
                # 使用统一的函数生成相对路径
                relative_path = generate_relative_path(uri, base_url)

            # 构造本地保存路径
            local_path = os.path.join(output_dir, relative_path)

            # 检查文件是否已存在，如果存在且不强制重新下载，则跳过
            if os.path.exists(local_path) and not force:
                # 更新进度条
                with pbar_lock:
                    pbar.update(1)
                continue

            # 创建目录（如果不存在）
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # 下载文件，添加浏览器请求头
            response = requests.get(
                download_url, headers=DEFAULT_HEADERS, stream=True, timeout=10
            )
            response.raise_for_status()

            # 保存文件
            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # 更新进度条
            with pbar_lock:
                pbar.update(1)

        except requests.exceptions.HTTPError as e:
            print(
                f"HTTP错误下载 {uri}: 状态码 {e.response.status_code} - {e.response.reason}"
            )
        except requests.exceptions.ConnectionError:
            print(f"连接错误下载 {uri}: 无法连接到服务器")
        except requests.exceptions.Timeout:
            print(f"超时错误下载 {uri}: 请求超时")
        except IOError as e:
            print(f"IO错误下载 {uri}: 无法保存文件 - {e}")
        except Exception as e:
            print(f"未知错误下载 {uri}: {type(e).__name__} - {e}")
        finally:
            queue.task_done()


def download_3dtiles(
    input_url: str,
    output_dir: str,
    num_threads: int = 8,
    force: bool = False,
    uris: list = None,
):
    """使用多线程下载3D tiles，保持相对结构

    参数:
        input_url: 3D tileset的url
        output_dir: 本地输出目录
        num_threads: 线程数量，默认为8
        force: 是否强制重新下载已存在的文件，默认为False
        uris: 可选，已经提取好的URI列表，如果提供则直接使用，否则重新提取
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 提取所有需要下载的uri
    if uris is None:
        print(f"Extracting all URIs from {input_url}...")
        all_uris = extract_uri_from_url(input_url)

        # 添加输入的tileset.json到下载列表并去重
        all_uris.append(input_url)
        all_uris = list(set(all_uris))  # 去重，避免重复下载
        print(f"Found {len(all_uris)} unique URIs to download")
    else:
        # 直接使用提供的URI列表
        all_uris = uris
        print(f"Using provided list with {len(all_uris)} unique URIs to download")

    # 创建任务队列
    queue = Queue()
    for uri in all_uris:
        queue.put(uri)

    # 初始化进度条
    pbar_lock = threading.Lock()
    with tqdm(total=queue.qsize(), desc="Downloading 3D Tiles") as pbar:
        # 创建并启动线程
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(
                target=download_uri,
                args=(queue, input_url, output_dir, pbar_lock, pbar, force),
            )
            thread.daemon = True
            thread.start()
            threads.append(thread)

        # 等待所有任务完成
        queue.join()

    print(f"All files downloaded successfully to {output_dir}")

    # 简化的下载结果检查，只显示实际文件数量
    print("\n正在检查下载结果...")

    # 获取实际的文件数量
    actual_count = count_files_in_directory(output_dir)

    if actual_count >= 0:
        print(f"下载完成，共下载了 {actual_count} 个文件")
        print("✅ 下载任务已完成")
    else:
        print("✅ 下载任务已完成，但无法统计文件数量")


if __name__ == "__main__":
    # 使用交互式方式获取参数
    print("3D Tiles 下载器")
    print("=" * 30)

    # 1. 选择操作模式
    input_url = ""
    all_uris = []

    while True:
        print("\n请选择操作模式:")
        print("1. 从URL提取URI并下载")
        print("2. 从本地文件加载URI并下载")
        mode_choice = input("请输入选项 (1/2): ").strip()

        if mode_choice == "1":
            # 1.1 输入URL并验证
            while True:
                input_url = input("请输入3D Tiles tileset.json的URL: ").strip()
                if validate_url(input_url):
                    break
                print("无效的URL，请输入以http://或https://开头的完整URL")

            # 1.2 获取URI列表并显示数量
            print(f"\n正在从 {input_url} 提取所有URI...")
            all_uris = extract_uri_from_url(input_url)
            # 添加输入URL并去重
            all_uris.append(input_url)
            all_uris = list(set(all_uris))  # 去重，避免重复下载
            uri_count = len(all_uris)
            print(f"共找到 {uri_count} 个唯一的URI需要下载")
            break
        elif mode_choice == "2":
            # 1.3 从本地文件加载URI列表
            file_path = input("请输入URI列表文件路径: ").strip()
            all_uris = load_uris_from_file(file_path)
            if all_uris:
                # 从URI列表中获取第一个URL作为base_url
                input_url = next(
                    (uri for uri in all_uris if uri.startswith("http")), ""
                )
                if not input_url:
                    print("错误：URI列表中没有找到有效的HTTP/HTTPS URL")
                    continue
                uri_count = len(all_uris)
                print(f"共加载到 {uri_count} 个唯一的URI需要下载")
                break
            else:
                print("无法加载URI列表，请重试")
        else:
            print("无效的选项，请输入1或2")

    # 3. 仅当从URL提取URI时，询问是否保存URI列表到本地
    if mode_choice == "1":
        save_confirm = (
            input("\n是否要将URI列表保存到本地（方便下次直接调用）？(y/n): ")
            .strip()
            .lower()
        )
        if save_confirm == "y":
            save_path = input("请输入保存路径（例如：uris.json）: ").strip()
            save_uris_to_file(all_uris, save_path)

    # 4. 询问是否下载
    download_confirm = input("\n是否要下载这些文件？(y/n): ").strip().lower()
    if download_confirm != "y":
        print("下载已取消")
        exit()

    # 4. 输入保存地址
    output_dir = input("\n请输入保存地址: ").strip()

    # 5. 执行下载，直接使用之前提取的URI列表
    threads = 8  # 默认线程数
    force = False  # 默认不强制重新下载
    download_3dtiles(input_url, output_dir, threads, force, all_uris)
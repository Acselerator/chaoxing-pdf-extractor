import os
import time
import sys
import io
import requests
import img2pdf
import re
from selenium import webdriver

# 强制设置标准输出为 UTF-8，解决 Windows 终端乱码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 配置
OUTPUT_DIR = "downloads"
# 登录页面
LOGIN_URL = "https://passport2.chaoxing.com/login?fid=&newversion=true&refer=http%3A%2F%2Fi.chaoxing.com"
# 目标课程页面 (用户指定)
TARGET_COURSE_URL = "https://mooc2-ans.chaoxing.com/mooc2-ans/mycourse/stu?courseid=256450797&clazzid=130453108&cpi=338099829&enc=8a3edf50ac1b05b64db238eed60da6c4&t=1767000829147&pageHeader=1&v=0&hideHead=0"

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def download_image(url, session, headers):
    try:
        response = session.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.content
    except Exception as e:
        print(f"Error downloading image {url}: {e}")
    return None

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 选择浏览器
    print("请选择浏览器:")
    print("1. Edge (默认)")
    print("2. Chrome")
    choice = input("请输入选项 (1/2): ").strip()

    if choice == '2':
        browser_name = "Chrome"
        options = webdriver.ChromeOptions()
    else:
        browser_name = "Edge"
        options = webdriver.EdgeOptions()

    # 初始化浏览器配置
    # options.add_argument('--headless') # 调试时建议关闭headless
    options.add_argument('--start-maximized')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    # 忽略证书错误
    options.add_argument('--ignore-certificate-errors')
    # 屏蔽日志
    options.add_argument("--log-level=3")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    print(f"正在启动浏览器({browser_name})...")
    try:
        if browser_name == "Chrome":
            # Chrome 使用 webdriver_manager 自动管理驱动
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        else:
            # Edge 尝试直接启动 (使用系统路径或当前目录下的 msedgedriver.exe)
            driver = webdriver.Edge(options=options)
    except Exception as e:
        print("\n" + "!"*50)
        print(f"【错误】无法启动 {browser_name} 浏览器驱动！")
        if browser_name == "Chrome":
             print(f"原因：自动下载/查找 chromedriver 失败。可能是网络问题或版本不匹配。")
             print("解决方案：")
             print("1. 请访问 https://googlechromelabs.github.io/chrome-for-testing/")
             print("2. 下载与您 Chrome 浏览器版本一致的 chromedriver.exe")
             print(f"3. 将 chromedriver.exe 放到本脚本所在目录: {os.getcwd()}")
        else:
             print(f"原因：未找到 msedgedriver.exe，或者版本不匹配。")
             print("解决方案：")
             print("1. 请访问 https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
             print("2. 下载与您 Edge 浏览器版本一致的 msedgedriver.exe")
             print(f"3. 将 msedgedriver.exe 放到本脚本所在目录: {os.getcwd()}")
        
        print("!"*50 + "\n")
        raise e
    
    try:
        print(f"正在打开登录页面: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        
        print("\n" + "="*50)
        print("【操作指南】")
        print("1. 请在浏览器中完成登录。")
        print("2. 登录成功后，请回到这里按回车键。")
        print("3. 脚本将自动跳转到目标课程页面并开始下载。")
        print("="*50 + "\n")
        input("登录完成请按回车键继续...")

        print(f"正在跳转到目标课程页面: {TARGET_COURSE_URL}")
        driver.get(TARGET_COURSE_URL)
        time.sleep(5) # 等待页面加载

        # --- 提取课程名称并创建对应文件夹 ---
        try:
            # 尝试获取课程名称
            # 1. 尝试从 title 获取
            course_title = driver.title
            # 2. 尝试查找常见的标题元素
            elements = driver.find_elements(By.CSS_SELECTOR, "h1, .courseName, .title, .f18")
            for elem in elements:
                if elem.text.strip() and len(elem.text.strip()) < 50: # 简单的长度过滤
                    course_title = elem.text.strip()
                    break
            
            # 清理文件名
            course_dir_name = sanitize_filename(course_title)
            if not course_dir_name:
                course_dir_name = "未命名课程"
            
            print(f"检测到课程名称: {course_title}")
            
            # 设置新的课程目录: downloads/课程名
            COURSE_DIR = os.path.join(OUTPUT_DIR, course_dir_name)
            if not os.path.exists(COURSE_DIR):
                os.makedirs(COURSE_DIR)
            print(f"文件将保存到: {COURSE_DIR}")
            
        except Exception as e:
            print(f"提取课程名称失败: {e}")
            COURSE_DIR = os.path.join(OUTPUT_DIR, "未知课程")
            if not os.path.exists(COURSE_DIR):
                os.makedirs(COURSE_DIR)
        # ---------------------------------------

        # 获取Cookies用于requests
        selenium_cookies = driver.get_cookies()
        session = requests.Session()
        headers = {
            "User-Agent": driver.execute_script("return navigator.userAgent;")
        }
        for cookie in selenium_cookies:
            session.cookies.set(cookie['name'], cookie['value'])

        # 1. 解析侧边栏获取所有章节链接
        print("正在解析当前页面的章节列表...")
        current_url = driver.current_url
        print(f"当前页面URL: {current_url}")
        
        # 检查是否需要切换到 frame_content-zj (针对 mooc2-ans)
        try:
            # 先尝试找 iframe
            iframe = driver.find_element(By.ID, "frame_content-zj")
            print("检测到 frame_content-zj，正在切换...")
            driver.switch_to.frame(iframe)
            # 等待 iframe 内容加载
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "chapter_item"))
            )
        except:
            print("未检测到 frame_content-zj 或切换失败，将在主页面查找...")

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        chapter_links = []

        # --- 策略: 提取隐藏域参数 + 解析 onclick ---
        # 1. 提取全局参数
        try:
            g_courseId = soup.find('input', id='courseId')['value']
            g_clazzId = soup.find('input', id='clazzId')['value']
            g_cpi = soup.find('input', id='cpi')['value']
            g_enc = soup.find('input', id='enc')['value']
            print(f"提取到关键参数: courseId={g_courseId}, clazzId={g_clazzId}, cpi={g_cpi}, enc={g_enc}")
        except Exception as e:
            print(f"提取全局参数失败: {e}，将尝试从链接中提取或使用默认值")
            g_courseId, g_clazzId, g_cpi, g_enc = "", "", "", ""

        # 2. 遍历 chapter_item
        # 查找所有章节单元和子章节
        # 注意：BeautifulSoup find_all 按照文档顺序返回
        all_elements = soup.find_all('div', class_=['chapter_unit', 'chapter_item'])
        print(f"找到 {len(all_elements)} 个结构元素，开始解析...")
        
        current_chapter_title = "杂项" # 默认文件夹

        for elem in all_elements:
            classes = elem.get('class', [])
            
            if 'chapter_unit' in classes:
                # 提取章节标题
                # 通常在 h3 > span.catalog_title 或 div.catalog_title
                # 或者直接在 div 中
                title_ele = elem.find(class_='catalog_title') or elem.find(class_='catalog_sbar')
                if title_ele:
                    current_chapter_title = title_ele.get_text(strip=True)
                else:
                    current_chapter_title = elem.get_text(strip=True)
                
                # 清理文件夹名称
                current_chapter_title = sanitize_filename(current_chapter_title)
                print(f"发现章节: {current_chapter_title}")
                continue

            # 如果是 chapter_item，继续原来的逻辑
            item = elem
            # 提取标题
            # 尝试获取章节号
            chapter_num = ""
            num_span = item.find('span', class_='catalog_sbar')
            if num_span:
                chapter_num = num_span.get_text(strip=True)
            
            # 尝试获取章节标题
            # 优先从 title 属性获取
            title_text = item.get('title')
            if not title_text:
                # 如果没有 title 属性，尝试找 catalog_title 类
                title_span = item.find('span', class_='catalog_title')
                if title_span:
                    title_text = title_span.get_text(strip=True)
                else:
                    # 否则获取全部文本
                    title_text = item.get_text(strip=True)
            
            # 组合标题
            if chapter_num:
                # 避免重复拼接
                if title_text and not title_text.strip().startswith(chapter_num):
                     title = f"{chapter_num} {title_text}"
                else:
                     title = title_text
            else:
                title = title_text
            
            title = re.sub(r'\s+', ' ', title).strip()
            
            # 提取 onclick 中的 chapterId
            # onclick="toOld('254798365', '1027046204', '126293182',0)"
            onclick = item.get('onclick')
            if onclick and 'toOld' in onclick:
                args = re.findall(r"'([^']*)'", onclick)
                if len(args) >= 2:
                    # toOld 参数顺序通常是: courseId, chapterId, clazzId
                    # 但有时候可能是 chapterId 在前，需根据实际值判断
                    # 根据源码: toOld('254798365', '1027046204', '126293182',0)
                    # 第一个是 courseId (254798365), 第二个是 chapterId (1027046204)
                    
                    cid = args[1]
                    
                    # 构造 URL
                    # 格式: https://mooc1.chaoxing.com/mycourse/studentstudy?chapterId={cid}&courseId={courseId}&clazzid={clazzId}&cpi={cpi}&enc={enc}&mooc2=1&hidetype=0
                    full_url = f"https://mooc1.chaoxing.com/mycourse/studentstudy?chapterId={cid}&courseId={g_courseId}&clazzid={g_clazzId}&cpi={g_cpi}&enc={g_enc}&mooc2=1&hidetype=0"
                    
                    if not any(c.get('cid') == cid for c in chapter_links):
                        chapter_links.append({'title': title, 'url': full_url, 'cid': cid, 'folder': current_chapter_title})
            
            # 备用: 如果没有 onclick，尝试找 href
            elif item.get('href') and 'studentstudy' in item.get('href'):
                 href = item['href']
                 if href.startswith('http'):
                    full_url = href
                 else:
                    full_url = "https://mooc1.chaoxing.com" + href if href.startswith('/') else href
                 
                 cid_match = re.search(r'chapterId=(\d+)', full_url)
                 cid = cid_match.group(1) if cid_match else full_url
                 
                 if not any(c.get('cid') == cid for c in chapter_links):
                    chapter_links.append({'title': title, 'url': full_url, 'cid': cid, 'folder': current_chapter_title})

        # 切回主文档
        driver.switch_to.default_content()

        print(f"共找到 {len(chapter_links)} 个章节链接。")
        
        if len(chapter_links) == 0:
            print("【警告】未找到任何章节链接！")
            print("可能的原因：")
            print("1. 页面结构发生了变化。")
            print("2. 侧边栏在 iframe 中但解析失败。")
            
            # 尝试检测 iframe 中的链接 (备用逻辑)
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                print(f"检测到 {len(iframes)} 个 iframe，尝试深入查找...")
                for iframe in iframes:
                    try:
                        driver.switch_to.frame(iframe)
                        soup_iframe = BeautifulSoup(driver.page_source, 'html.parser')
                        links_iframe = soup_iframe.find_all('a', href=True)
                        for link in links_iframe:
                            href = link['href']
                            if 'studentstudy' in href:
                                if href.startswith('http'):
                                    full_url = href
                                else:
                                    full_url = "https://mooc1.chaoxing.com" + href if href.startswith('/') else href
                                title = link.get_text(strip=True) or link.get('title') or "Unknown_Chapter"
                                if not any(c.get('url') == full_url for c in chapter_links):
                                    chapter_links.append({'title': title, 'url': full_url})
                        driver.switch_to.default_content()
                    except:
                        driver.switch_to.default_content()
                print(f"深入查找后，共找到 {len(chapter_links)} 个章节链接。")

        # 2. 遍历每个章节
            
            elements_with_onclick = soup.find_all(attrs={"onclick": True})
            for elem in elements_with_onclick:
                onclick_text = elem['onclick']
                # 匹配 getTeacherAjax('123', '456', '789')
                match = re.search(r"getTeacherAjax\(['\"](\d+)['\"],\s*['\"](\d+)['\"],\s*['\"](\d+)['\"]", onclick_text)
                if match:
                    c_id, course_id, clazz_id = match.groups()
                    # 构造URL
                    # 注意：这里需要保留原有的其他参数如 enc, cpi 等，为了简单起见，我们替换掉关键ID
                    # 更稳妥的方式是替换当前URL中的 chapterId
                    
                    # 简单的构造方式，可能缺少 enc 等参数导致 403，所以最好基于 START_URL 替换
                    new_url = START_URL
                    new_url = re.sub(r'chapterId=\d+', f'chapterId={c_id}', new_url)
                    new_url = re.sub(r'courseId=\d+', f'courseId={course_id}', new_url)
                    new_url = re.sub(r'clazzid=\d+', f'clazzid={clazz_id}', new_url)
                    
                    title = elem.get_text(strip=True) or elem.get('title') or f"Chapter_{c_id}"
                    if not any(c['url'] == new_url for c in chapter_links):
                        chapter_links.append({'title': title, 'url': new_url})

        # --- 策略 C: 查找 data-chapterid 属性 ---
        if not chapter_links:
             print("策略B未找到链接，尝试策略C (解析 data属性)...")
             elements_with_data = soup.find_all(attrs={"data-chapterid": True})
             for elem in elements_with_data:
                 c_id = elem['data-chapterid']
                 new_url = re.sub(r'chapterId=\d+', f'chapterId={c_id}', START_URL)
                 title = elem.get_text(strip=True) or f"Chapter_{c_id}"
                 if not any(c['url'] == new_url for c in chapter_links):
                        chapter_links.append({'title': title, 'url': new_url})

        print(f"共找到 {len(chapter_links)} 个章节链接。")
        
        # 如果还是没找到，询问是否下载当前页
        if not chapter_links:
            print("\n" + "!"*50)
            print("【警告】未找到任何章节列表！")
            print("可能是页面结构发生了变化，或者侧边栏未加载。")
            print("是否尝试仅下载当前页面内容？(y/n)")
            choice = input("请输入: ").strip().lower()
            if choice == 'y':
                chapter_links.append({'title': "Current_Page", 'url': driver.current_url})
            else:
                print("程序退出。")
                return

        # 2. 遍历每个章节
        for index, chapter in enumerate(chapter_links):
            print(f"\n[{index+1}/{len(chapter_links)}] 处理章节: {chapter['title']}")
            
            # 创建章节文件夹
            folder_name = chapter.get('folder', '杂项')
            chapter_dir = os.path.join(COURSE_DIR, folder_name)
            if not os.path.exists(chapter_dir):
                os.makedirs(chapter_dir)
            
            safe_title = sanitize_filename(chapter['title'])
            # 如果标题以数字开头（例如 "1.1 "），则直接使用标题作为文件名
            # 否则保留原来的索引前缀，以防顺序混乱
            if re.match(r'^\d', safe_title):
                pdf_filename = os.path.join(chapter_dir, f"{safe_title}.pdf")
            else:
                pdf_filename = os.path.join(chapter_dir, f"{index+1:02d}_{safe_title}.pdf")

            if os.path.exists(pdf_filename):
                print("  文件已存在，跳过。")
                continue

            driver.get(chapter['url'])
            time.sleep(3) # 等待页面加载

            # 寻找iframe
            # 学习通的内容通常在 iframe 中，可能有多个 tab
            # 我们需要找到包含 PPT/文档 的 iframe
            
            image_data_list = []
            
            # 获取所有iframe
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"  找到 {len(iframes)} 个iframe，正在检查内容...")
            
            # 优化：只检查第一个 iframe
            if iframes:
                iframes = [iframes[0]]
            
            for i, iframe in enumerate(iframes):
                try:
                    # 切换到iframe
                    driver.switch_to.frame(iframe)
                    time.sleep(2)
                    
                    # 检查是否有嵌套iframe (通常 content iframe 里面还有 iframe)
                    nested_iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    if nested_iframes:
                        print(f"    iframe {i} 中包含 {len(nested_iframes)} 个嵌套iframe，深入检查...")
                        for j, nested_iframe in enumerate(nested_iframes):
                            # 如果已经找到图片，跳过后续检查
                            if image_data_list:
                                break
                                
                            try:
                                driver.switch_to.frame(nested_iframe)
                                time.sleep(2)
                                
                                # 检查是否有 panView iframe (PPT阅读器)
                                pan_view_iframes = driver.find_elements(By.ID, "panView")
                                if pan_view_iframes:
                                    print(f"      在嵌套iframe {i}-{j} 中发现 panView，切换...")
                                    driver.switch_to.frame(pan_view_iframes[0])
                                    time.sleep(2)
                                    imgs = extract_images_from_current_frame(driver)
                                    if imgs:
                                        print(f"        在 panView 中找到 {len(imgs)} 张图片")
                                        image_data_list.extend(download_images(imgs, session, headers))
                                    driver.switch_to.parent_frame() # 回到 nested_iframe
                                else:
                                    # 检查是否有图片
                                    imgs = extract_images_from_current_frame(driver)
                                    if imgs:
                                        print(f"      在嵌套iframe {i}-{j} 中找到 {len(imgs)} 张图片")
                                        image_data_list.extend(download_images(imgs, session, headers))
                                    else:
                                        # 有时候还有第三层 iframe (例如 PPT 阅读器)
                                        deep_iframes = driver.find_elements(By.TAG_NAME, "iframe")
                                        if deep_iframes:
                                             for k, deep_iframe in enumerate(deep_iframes):
                                                driver.switch_to.frame(deep_iframe)
                                                time.sleep(2)
                                                
                                                imgs = extract_images_from_current_frame(driver)
                                                if imgs:
                                                    print(f"        在深层iframe {i}-{j}-{k} 中找到 {len(imgs)} 张图片")
                                                    image_data_list.extend(download_images(imgs, session, headers))
                                                driver.switch_to.parent_frame()

                                driver.switch_to.parent_frame()
                            except Exception as e:
                                print(f"      处理嵌套iframe {i}-{j} 出错: {e}")
                                try:
                                    driver.switch_to.parent_frame()
                                except:
                                    pass
                    else:
                        # 直接检查当前iframe
                        imgs = extract_images_from_current_frame(driver)
                        if imgs:
                            print(f"    在iframe {i} 中找到 {len(imgs)} 张图片")
                            image_data_list.extend(download_images(imgs, session, headers))
                            
                    driver.switch_to.default_content()
                    
                    # 如果已经找到图片，跳过后续iframe
                    if image_data_list:
                        break
                        
                except Exception as e:
                    print(f"  处理iframe {i} 时出错: {e}")
                    try:
                        driver.switch_to.default_content()
                    except:
                        pass

            if image_data_list:
                print(f"  正在生成PDF: {pdf_filename}")
                try:
                    with open(pdf_filename, "wb") as f:
                        f.write(img2pdf.convert(image_data_list))
                    print("  PDF生成成功！")
                except Exception as e:
                    print(f"  PDF生成失败: {e}")
            else:
                print("  未找到图片内容，可能是视频章节或纯文本。")

    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        print("程序结束。")
        # driver.quit() # 可以选择不关闭以便调试

def extract_images_from_current_frame(driver):
    """从当前frame提取可能的PPT图片URL"""
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    images = []
    
    # 策略: 查找所有 img 标签，并根据 src 特征过滤
    all_imgs = soup.find_all('img')
    for img in all_imgs:
        src = img.get('src') or img.get('data-src')
        if not src:
            continue
            
        # 补全 URL
        if not src.startswith('http'):
            if src.startswith('//'):
                src = "https:" + src
            elif src.startswith('/'):
                src = "https://mooc1.chaoxing.com" + src # 假设是这个域名，但也可能是 pan-yz
            else:
                # 相对路径，比较麻烦，先忽略或尝试拼接
                continue
        
        # 过滤逻辑
        # 1. 排除常见 UI 图标
        if any(x in src for x in ['/css/', '/images/', '/icon/', 'loading', 'button', 'logo']):
            continue
            
        # 2. 优先保留看起来像文档图片的链接
        # 用户提示: https://s3.ananas.chaoxing.com/doc/.../1.png
        if '/doc/' in src or 'ananas.chaoxing.com' in src:
            images.append(src)
        # 3. 如果没有明确特征，但看起来是图片，也可以保留 (可能需要更严格的过滤)
        elif 'preview' in src or 'thumb' in src:
             images.append(src)
    
    # 去重并保持顺序
    seen = set()
    ordered_images = []
    for img in images:
        if img not in seen:
            seen.add(img)
            ordered_images.append(img)
    return ordered_images

def download_images(img_urls, session, headers):
    data_list = []
    for url in img_urls:
        if not url.startswith('http'):
            url = "https:" + url
        content = download_image(url, session, headers)
        if content:
            data_list.append(content)
    return data_list

if __name__ == "__main__":
    main()


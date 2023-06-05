from pathlib import Path
from typing import Set, Tuple, Optional, Union

from app.core import settings, MetaInfo
from app.modules import _ModuleBase
from app.modules.qbittorrent.qbittorrent import Qbittorrent
from app.utils.string import StringUtils


class QbittorrentModule(_ModuleBase):
    qbittorrent: Qbittorrent = None

    def init_module(self) -> None:
        self.qbittorrent = Qbittorrent()

    def init_setting(self) -> Tuple[str, Union[str, bool]]:
        return "DOWNLOADER", "qbittorrent"

    def download(self, torrent_path: Path, cookie: str,
                 episodes: Set[int] = None) -> Optional[Tuple[Optional[str], str]]:
        """
        根据种子文件，选择并添加下载任务
        :param torrent_path:  种子文件地址
        :param cookie:  cookie
        :param episodes:  需要下载的集数
        :return: 种子Hash
        """
        if not torrent_path.exists():
            return None, f"种子文件不存在：{torrent_path}"
        # 生成随机Tag
        tag = StringUtils.generate_random_str(10)
        # 如果要选择文件则先暂停
        is_paused = True if episodes else False
        # 添加任务
        state = self.qbittorrent.add_torrent(content=torrent_path.read_bytes(),
                                             download_dir=settings.DOWNLOAD_PATH,
                                             is_paused=is_paused,
                                             tag=tag,
                                             cookie=cookie)
        if not state:
            return None, f"添加种子任务失败：{torrent_path}"
        else:
            # 获取种子Hash
            torrent_hash = self.qbittorrent.get_torrent_id_by_tag(tag=tag)
            if not torrent_hash:
                return None, f"获取种子Hash失败：{torrent_path}"
            else:
                if is_paused:
                    # 种子文件
                    torrent_files = self.qbittorrent.get_files(torrent_hash)
                    if not torrent_files:
                        return torrent_hash, "获取种子文件失败，下载任务可能在暂停状态"

                    # 不需要的文件ID
                    file_ids = []
                    # 需要的集清单
                    sucess_epidised = []

                    for torrent_file in torrent_files:
                        file_id = torrent_file.get("id")
                        file_name = torrent_file.get("name")
                        meta_info = MetaInfo(file_name)
                        if not meta_info.get_episode_list() \
                                or not set(meta_info.get_episode_list()).issubset(episodes):
                            file_ids.append(file_id)
                        else:
                            sucess_epidised = list(set(sucess_epidised).union(set(meta_info.get_episode_list())))
                    if sucess_epidised and file_ids:
                        # 选择文件
                        self.qbittorrent.set_files(torrent_hash=torrent_hash, file_ids=file_ids, priority=0)
                    # 开始任务
                    self.qbittorrent.start_torrents(torrent_hash)
                    return torrent_hash, f"添加下载成功，已选择集数：{sucess_epidised}"
                else:
                    return torrent_hash, "添加下载成功"
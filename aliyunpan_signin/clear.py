import httpx
import logging

from .utils import updateAccesssToken, send_notify

logging = logging.getLogger("__adrive__")

class ClearFile:
    def __init__(self):
        self.access_token = ''
        self.drive_id = ''
        self.xiaoya_refresh_token = ''
        self.xiaoya_folder_id = ''
        self.uid = ''
        self.channel_item = ''

    def config(self,
               xiaoya_refresh_token,
               xiaoya_folder_id,
               uid=None,
               channel_item=None
               ):
        self.xiaoya_refresh_token = xiaoya_refresh_token
        self.xiaoya_folder_id = xiaoya_folder_id
        self.uid = uid
        self.channel_item = channel_item

    def get_drive_user_info(self, access_token):
        url = f"https://user.aliyundrive.com/v2/user/get"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        data = {}
        try:
            res = httpx.post(url=url, headers=headers, json=data)
            if res.status_code == 200:
                res_json = res.json()
                self.drive_id = res_json["resource_drive_id"]
        except Exception as e:
            logging.error(f"「阿里云盘工具箱」获取用户信息出错，{e}", exc_info=True)

    def get_file_list(self, folder_id):
        url = f"https://api.aliyundrive.com/adrive/v3/file/list"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "drive_id": self.drive_id,
            "parent_file_id": folder_id
        }
        try:
            file_list = []
            file_id_list = []
            file_size_org_list = []
            res = httpx.post(url, headers=headers, json=data)
            if res.status_code == 200:
                json_load = res.json()
                for file_item in json_load.get("items"):
                    if file_item.get("type") == "file":
                        file_name = file_item.get("name")

                        file_size_org = file_item.get("size")

                        file_size = self.format_file_size(file_size_org)
                        file_id = file_item.get("file_id")
                        file_info = f"{file_name} -> {file_size}"
                        file_list.append(file_info)
                        file_id_list.append(file_id)

                        file_size_org_list.append(file_size_org)
                    elif file_item.get("type") == "folder":
                        if file_item.get("name") not in ['配置文件示范','常用软件']:
                            file_id_list.append(file_item.get("file_id"))

                total_size = sum(int(item) for item in file_size_org_list)
                total_size = self.format_file_size(total_size)

                logging.info(f"「阿里云盘工具箱」小雅资源盘文件列表：{file_list}")
                return file_id_list, file_list, total_size
        except Exception as e:
            logging.error(f"「阿里云盘工具箱」获取文件列表出错：{e}", exc_info=True)

    @staticmethod
    def format_file_size(file_size):
        units = ['B', 'KB', 'MB', 'GB', 'TB']

        for unit_index, unit in enumerate(units):
            if file_size < 1024 or unit_index == len(units) - 1:
                break
            file_size /= 1024

        return f'{file_size:.2f} {units[unit_index]}'

    def move_file_to_trash(self, file_id_list, file_list):
        url = "https://api.aliyundrive.com/v2/recyclebin/trash"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        for file_index, file_id in enumerate(file_id_list):
            data = {
                "drive_id": self.drive_id,
                "file_id": file_id
            }
            try:
                res = httpx.post(url, headers=headers, json=data)
                if res.status_code == 204:
                    # print(f"删除「{file_list[file_index]}」成功")
                    continue
            except Exception as e:
                logging.error(f"「阿里云盘工具箱」移动至回收站出错：{e}", exc_info=True)
        logging.info(f"「阿里云盘工具箱」小雅转存文件夹已清空文件。")

    def clear_recycle(self, file_id_list):
        url = "https://api.aliyundrive.com/v3/file/delete"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        for file_id in file_id_list:
            data = {
                "drive_id": self.drive_id,
                "file_id": file_id
            }
            try:
                res = httpx.post(url, headers=headers, json=data)
                if res.status_code == 202:
                    continue
            except Exception as e:
                logging.error(f"「阿里云盘工具箱」清理回收站出错：{e}", exc_info=True)
        logging.info(f"「阿里云盘工具箱」已清理资源盘回收站")

    def main(self):
        try:
            nick_name, refresh_token, self.access_token = updateAccesssToken(self.xiaoya_refresh_token)
            self.get_drive_user_info(self.access_token)
            file_id_list, file_list, total_size = self.get_file_list(folder_id=self.xiaoya_folder_id)
            if file_list:
                self.move_file_to_trash(file_id_list=file_id_list, file_list=file_list)
                self.clear_recycle(file_id_list=file_id_list)

                title = f"小雅已清理 {len(file_list)}个文件 共 {total_size}"
                if len(file_list) > 1:
                    content = '\n'.join([f"• {item}" for item in file_list])
                else:
                    content = '\n'.join(file_list)
                send_notify(title, content, self.uid, self.channel_item)
        except Exception as e:
            logging.error(f"「阿里云盘工具箱」清理资源盘出错了，{e}", exc_info=True)
            raise e
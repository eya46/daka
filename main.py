import hashlib
from typing import Union, Optional

import httpx

url_main = "https://某个网址/"

url_index = url_main + "student/index"

url_login = url_main + "student/website/login"

url_last_info = url_main + "student/content/student/temp/zzdk/lastone"

url_send_daka = url_main + "student/content/student/temp/zzdk"

time_out = httpx.Timeout(4.0)

headers = {
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, "
                  "like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
}

xgym_dm = {
    '0': '未接种',
    '1': '已接种未完成',
    '2': '已接种已完成',
    '3': '已接种加强针',
    '4': '未接种加强针',
}


def md5(passwd: str) -> str:
    temp = hashlib.md5()
    temp.update(str(passwd).encode())
    temp = temp.hexdigest()
    return temp[:5] + 'a' + temp[5:9] + 'b' + temp[9:-2]


async def login(r: httpx.AsyncClient, account: str, password: str) -> Union[bool, str]:
    try:
        await r.get(
            "https://xgyyx.njpi.edu.cn/student/index",
            headers=headers,
            timeout=time_out
        )

        _res = await r.post(
            url_login,
            headers=headers,
            data={
                'uname': account,
                'pd_mm': md5(password)
            },
            timeout=time_out
        )

        __data = _res.json()

        if __data.get("goto2") is not None:
            return True
        else:
            if (_res := __data.get("msg")) is None:
                return "解析登录失败原因失败"
            else:
                return _res
    except (httpx.ReadTimeout, httpx.ConnectTimeout):
        return False


# True登录成功，False超时，str:登录失败:原因
async def login_now(account: str, password: str) -> Union[bool, str]:
    r = httpx.AsyncClient()
    try:
        return await login(r, account, password)
    except (httpx.ReadTimeout, httpx.ConnectTimeout):
        return False
    finally:
        await r.aclose()


async def last_info(r: httpx.AsyncClient):
    try:
        _res = await r.get(
            url_last_info, headers=headers,
            timeout=time_out
        )
        return _res.json()
    except (httpx.ReadTimeout, httpx.ConnectTimeout):
        return False


def build_form(data: dict) -> Optional[dict]:
    def _build(key: str) -> str:
        if key.startswith("!"):
            try:
                __temp = data
                for __i in key[1:].split('.'):
                    __temp = __temp[__i]
                return __temp if __temp is not None else ""
            except:
                return ""
        else:
            return key

    xgym_true_dm = "2" if data.get("xgym", "2") is None else data.get("xgym", "2")

    try:
        _temp = {'dkdz': "!dkdz",
                 'dkly': 'baidu',
                 'dkd': "!dkd",
                 'jzdValue': f'{data["jzdSheng"]["dm"]},{data["jzdShi"]["dm"]},{data["jzdXian"]["dm"]}',
                 'jzdSheng.dm': '!jzdSheng.dm',
                 'jzdShi.dm': '!jzdShi.dm',
                 'jzdXian.dm': '!jzdXian.dm',
                 'jzdDz': '!jzdDz',
                 'jzdDz2': '!jzdDz2',
                 'lxdh': '!lxdh',
                 'sfzx': '!sfzx',
                 'sfzx1': '不在校' if data["sfzx"] != "1" else "在校",
                 'twM.dm': '!twM.dm',
                 'tw1': '!twM.mc',
                 'yczk.dm': '!yczk.dm',
                 'yczk1': '!yczk.mc',
                 'fbrq': '!fbrq',
                 'jzInd': '!jzInd',
                 'jzYy': '!jzYy',
                 'zdjg': '!zdjg',
                 'fxrq': '!fxrq',
                 'brStzk.dm': '!brStzk.dm',
                 'brStzk1': '!brStzk.mc',
                 'brJccry.dm': '!brJccry.dm',
                 'brJccry1': '!brJccry.mc',
                 'jrStzk.dm': '!jrStzk.dm',
                 'jrStzk1': '!jrStzk.mc',
                 'jrJccry.dm': '!jrJccry.dm',
                 'jrJccry1': '!jrJccry.mc',
                 'xgym': '!xgym',
                 'xgym1': xgym_dm[xgym_true_dm],
                 'hsjc': '!hsjc',
                 'hsjc1': '',
                 'bz': '!bz',
                 'operationType': 'Create',
                 'dm': ''}

        for i in _temp:
            _temp[i] = _build(_temp[i])

        return _temp
    except Exception as e:
        return None


async def post_daka(r: httpx.AsyncClient, form: dict) -> str:
    try:
        _res = await r.post(
            url_send_daka,
            headers=headers,
            data=form,
            timeout=time_out
        )

        if "重复提交" in _res.text:
            return "打卡失败 -> 今日已打卡"
        elif "message" in _res.text:
            __temp = "打卡失败 -> 错误如下:\n"
            # print(_res.text)
            for i in (await _res.json())['errorInfoList']:
                __temp += f"{i['message']}\n"
            return __temp[:-1]
        else:
            return f"打卡成功! -> 地点:{form['dkd']}"
    except (httpx.ReadTimeout, httpx.ConnectTimeout):
        return "打卡失败 -> 提交打卡超时"
    except:
        return "打卡失败 -> 提交打卡出现未知错误"


async def daka(account: str, password: str) -> str:
    r = httpx.AsyncClient()
    try:
        login_res = await login(r, account, password)
        if isinstance(login_res, str):
            return f"打卡失败 -> {login_res}"
        if isinstance(login_res, bool) and not login_res:
            return f"打卡失败 -> 打卡网站超时"

        the_last_info = await last_info(r)

        if isinstance(the_last_info, bool):
            return "打卡失败 -> 获取上次打卡信息超时"

        form = build_form(the_last_info)

        if not form:
            return "打卡失败 -> 构建打卡信息失败"

        return await post_daka(r, form)
    except (httpx.ReadTimeout, httpx.ConnectTimeout):
        return "打卡失败 -> 打卡网站超时"
    except httpx.ConnectError:
        return "打卡失败 -> 打卡网站连接失败"
    except Exception as e:
        return f"打卡失败 -> 打卡函数未知错误:{e}"
    finally:
        await r.aclose()


if __name__ == '__main__':
    import asyncio

    print(asyncio.run(
        daka("2xxxxxxxxx", "abcdefg")
    ))

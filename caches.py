from typing import Union, List

class WaveformDataCache:
    def __init__(self):
        self.cache: dict[int, dict[int, List]] = {}
        self.received_count: dict[int, int] = {}

    def add_data(self, recId: int, idx: int, cnt: int, data: List) -> Union[List, None]:
        if recId not in self.cache:
            self.cache[recId] = {}
            self.received_count[recId] = 0  # 初始化接收计数

        if idx not in self.cache[recId]:
            self.cache[recId][idx] = data
            self.received_count[recId] += 1  # 增加接收计数
            print(f"已接收到包 {self.received_count[recId]} / {cnt}")

        if len(self.cache[recId]) == cnt:
            all_data = []
            for i in range(1, cnt + 1):
                if i in self.cache[recId]:
                    all_data.extend(self.cache[recId][i])
            return all_data

        return None


class PhotoDataCache:
    def __init__(self):
        self.cache: dict[tuple[int, float, int], dict[int, bytes]] = {}
        self.received_count: dict[tuple[int, float, int], int] = {}

    def add_data(self, recId: int, flawPos: float, cameraIdx: int, packIdx: int, packCnt: int,
                 data: bytes) -> Union[bytes, None]:
        key = (recId, flawPos, cameraIdx)
        if key not in self.cache:
            self.cache[key] = {}
            self.received_count[key] = 0  # 初始化接收计数

        if packIdx not in self.cache[key]:
            self.cache[key][packIdx] = data
            self.received_count[key] += 1  # 增加接收计数
            print(f"已接收到包 {self.received_count[key]} / {packCnt}")

        if len(self.cache[key]) == packCnt:
            full_data = b''.join(self.cache[key][i] for i in sorted(self.cache[key].keys()))
            del self.cache[key]
            del self.received_count[key]  # 清除计数
            return full_data

        return None


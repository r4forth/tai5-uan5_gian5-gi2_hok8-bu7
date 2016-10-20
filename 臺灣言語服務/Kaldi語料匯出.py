# -*- coding: utf-8 -*-
import json
from os import makedirs
from os.path import join, isdir
from shutil import rmtree


from 臺灣言語資料庫.資料模型 import 影音表
from 臺灣言語工具.系統整合.程式腳本 import 程式腳本
from 臺灣言語工具.解析整理.拆文分析器 import 拆文分析器
from 臺灣言語工具.語言模型.KenLM語言模型訓練 import KenLM語言模型訓練
from 臺灣言語服務.漢語語音處理 import 漢語語音處理
from 臺灣言語工具.基本物件.公用變數 import 標點符號
from 臺灣言語工具.基本物件.公用變數 import 無音


class Kaldi語料匯出(程式腳本):
    環境噪音 = 'NSN\tNSN'

    @classmethod
    def 初使化辭典資料(cls):
        return {
            '全部詞': {'SIL\tSIL', '<UNK>\tSPN', 'SPN\tSPN'},
            '全部句': [],
            '聲類': set(),
            '韻類': {},
            '調類': {},
        }

    @classmethod
    def 匯出一種語言語料(cls, 語言, 音標系統, 輸出試驗音檔, 語料資料夾, 資料夾名, 辭典資料):
        訓練語料資料夾 = join(語料資料夾, 資料夾名, 'train')
        if isdir(訓練語料資料夾):
            rmtree(訓練語料資料夾)
        makedirs(訓練語料資料夾, exist_ok=True)
        with cls._寫檔(訓練語料資料夾, 'text') as 聽拍內容:
            with cls._寫檔(訓練語料資料夾, 'wav.scp') as 音檔目錄:
                with cls._寫檔(訓練語料資料夾, 'segments') as 語句目錄:
                    with cls._寫檔(訓練語料資料夾, 'reco2file_and_channel') as 音檔對應頻道:
                        with cls._寫檔(訓練語料資料夾, 'utt2spk') as 語句對應語者:
                            cls._揣影音輸出(
                                語言, 音標系統, 輸出試驗音檔,
                                聽拍內容, 音檔目錄, 語句目錄, 音檔對應頻道, 語句對應語者, 辭典資料
                            )

    @classmethod
    def 辭典資料載入語句文本(cls, 語言文本, 音標系統, 辭典資料):
        for 一逝 in cls._讀檔案(語言文本):
            這擺參數 = {'音標系統': 音標系統, '一逝': 一逝}
            這擺參數.update(辭典資料)
            cls._資料加到辭典(**這擺參數)

    @classmethod
    def 匯出辭典資料(cls, 辭典資料, 語料資料夾, 資料夾名):
        訓練語料資料夾 = join(語料資料夾, 資料夾名, 'local', 'dict')
        if isdir(訓練語料資料夾):
            rmtree(訓練語料資料夾)
        makedirs(訓練語料資料夾, exist_ok=True)
        cls._陣列寫入檔案(join(訓練語料資料夾, 'optional_silence.txt'), ["SIL"])
        cls._陣列寫入檔案(join(訓練語料資料夾, 'lexicon.txt'), sorted(辭典資料['全部詞']))

        安靜噪音集 = ["SIL", "SPN"]
        if cls.環境噪音 in 辭典資料['全部詞']:
            安靜噪音集.append("NSN")
        cls._陣列寫入檔案(join(訓練語料資料夾, 'silence_phones.txt'), 安靜噪音集)

        聲韻類 = 辭典資料['聲類'].copy()
        for 仝韻 in 辭典資料['韻類'].values():
            聲韻類.add(' '.join(sorted(仝韻)))
        cls._陣列寫入檔案(join(訓練語料資料夾, 'nonsilence_phones.txt'), sorted(聲韻類))

        調問題 = {' '.join(安靜噪音集)}
        for 仝調 in 辭典資料['調類'].values():
            調問題.add(' '.join(sorted(仝調)))
        cls._陣列寫入檔案(join(訓練語料資料夾, 'extra_questions.txt'), sorted(調問題))

    @classmethod
    def 匯出語言模型(cls, 語言文本, 語料資料夾, 資料夾名):
        訓練語料資料夾 = join(語料資料夾, 資料夾名, 'local', 'lm')
        if isdir(訓練語料資料夾):
            rmtree(訓練語料資料夾)
        makedirs(訓練語料資料夾, exist_ok=True)
        KenLM語言模型訓練().訓練([語言文本], 訓練語料資料夾)

    @classmethod
    def _資料加到辭典(cls, 聲類, 韻類, 調類, 全部詞, 全部句, 一逝, 音標系統):
        句物件 = 拆文分析器.分詞句物件(一逝)
        一句 = []
        外來語數量 = 0
        for 詞物件 in 句物件.網出詞物件():
            分詞 = 詞物件.看分詞()
            try:
                聲韻陣列 = []
                for 字物件 in 詞物件.轉音(音標系統, '音值').篩出字物件():
                    聲, 韻, 調 = 字物件.音
                    聲韻陣列.append(聲)
                    聲類.add(聲)
                    for 一个音素 in 漢語語音處理.切漢語韻(韻):
                        一个音素調 = 一个音素 + 調
                        聲韻陣列.append(一个音素調)
                        try:
                            韻類[一个音素].add(一个音素調)
                        except:
                            韻類[一个音素] = {一个音素調}
                        try:
                            調類[調].add(一个音素調)
                        except:
                            調類[調] = {一个音素調}
                一項 = '{}\t{}'.format(分詞, ' '.join(聲韻陣列))
                全部詞.add(一項)
            except:
                字物件陣列 = 詞物件.篩出字物件()
                if (
                    len(字物件陣列) == 1 and
                    字物件陣列[0].型 == "NSN" and
                    字物件陣列[0].音 == 無音
                ):
                    全部詞.add(cls.環境噪音)
                elif (
                    len(字物件陣列) == 1 and
                    (字物件陣列[0].型 in 標點符號 or 字物件陣列[0].型 == "'") and
                    (字物件陣列[0].音 in 標點符號 or 字物件陣列[0].音 in {無音, "'"})
                ):
                    一項 = '{}\tSIL'.format(分詞)
                    全部詞.add(一項)
                else:
                    一項 = '{}\tSPN'.format(分詞)
                    外來語數量 += 1
#                     全部詞.add(一項)
            一句.append(分詞)
        全部句.append(' '.join(一句))
        return len(一句), 外來語數量

    @classmethod
    def _揣影音輸出(cls, 語言, 音標系統, 輸出試驗音檔,
               聽拍內容, 音檔目錄, 語句目錄, 音檔對應頻道, 語句對應語者, 辭典資料):
        第幾个 = 0
        for 第幾个, 影音 in enumerate(
            影音表.objects
            .distinct()
            .filter(影音聽拍__isnull=False)
            .filter(語言腔口__語言腔口=語言)
            .order_by('pk')
        ):
            音檔名 = 'tong{0:07}'.format(第幾个)
            print(
                音檔名,
                'sox -G {} -b 16 -c 1 -r 16k -t wav - | '.format(影音.影音所在()),
                file=音檔目錄
            )
#             sw02001-A sw02001 A
            print(音檔名, 音檔名, 'A', file=音檔對應頻道)
            音檔長度 = 影音.聲音檔().時間長度()
            聽拍 = cls._揣上尾的聽拍(影音.影音聽拍.first().聽拍)
            語者名對應輸出名 = {}
            這馬幾个人 = 0
            for 第幾句, 一句聽拍 in enumerate(json.loads(聽拍.聽拍資料)):
                開始 = float(一句聽拍['開始時間'])
                結束 = float(一句聽拍['結束時間'])
                if 0.0 <= 開始 and 開始 + 0.1 < 結束 and 結束 <= 音檔長度:
                    if 一句聽拍['語者'] == '無註明':
                        語者 = '{}-{:07}無註明'.format(音檔名, 這馬幾个人)
                        這馬幾个人 += 1
                    else:
                        語者名 = ''.join(一句聽拍['語者'].split())
                        try:
                            語者 = 語者名對應輸出名[語者名]
                        except:
                            語者 = '{}-{:07}{}'.format(
                                音檔名, 這馬幾个人, 語者名
                            )
                            這馬幾个人 += 1
                            語者名對應輸出名[語者名] = 語者
                    語句名 = '{0}-ku{1:07}'.format(語者, 第幾句)
                    內容 = 一句聽拍['內容']
                    這擺參數 = {'音標系統': 音標系統, '一逝': 內容}
                    這擺參數.update(辭典資料)
                    詞數量, 外來語數量 = cls._資料加到辭典(**這擺參數)
#                     詞數量, 外來語數量 = cls._資料加到辭典(音標系統=音標系統,一逝=內容, **辭典資料,)
                    if not 輸出試驗音檔 and 詞數量 <= 外來語數量 * 3:
                        continue
                    print(語句名, 內容, file=聽拍內容)
    #                 sw02001-A_000098-001156 sw02001-A 0.98 11.56
                    print(語句名, 音檔名, 一句聽拍['開始時間'], 一句聽拍['結束時間'], file=語句目錄)
                    print(語句名, 語者, file=語句對應語者)
        for 第幾个, 影音 in enumerate(
            影音表.objects
            .distinct()
            .filter(影音聽拍__isnull=True)
            .filter(影音文本__isnull=False)
            .filter(語言腔口__語言腔口=語言),
            start=第幾个
        ):
            cls._揣上尾的文本(影音.影音文本.first().文本)

    @classmethod
    def _揣上尾的聽拍(cls, 聽拍):
        try:
            while True:
                聽拍 = 聽拍.聽拍校對.first().新聽拍
        except:
            return 聽拍

    @classmethod
    def _揣上尾的文本(cls, 文本):
        try:
            while True:
                文本 = 文本.文本校對.first().新文本
        except:
            return 文本

    @classmethod
    def _寫檔(cls, 資料夾, 檔名):
        return open(join(資料夾, 檔名), 'w')

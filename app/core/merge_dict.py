import copy


def MergeDict(lft: dict, rgt: dict) -> dict:
    """
    右辞書を左辞書にマージし、修正された左辞書を返す。
    この関数は、オプションコマンドを含むキーを処理することで、`rgt`を`lft`にマージします。
    `rgt`のキーには、マージの動作を制御するために"!"で区切られたコマンドプレフィックスを含めることができます。
    コマンドプレフィックス（"!"で分離されてキーに付加される）:
    - "a"（append）：辞書の場合は、ネストされた辞書を再帰的にマージします。リストの場合は、リストを拡張します。
    - "d"（delete）：`lft`からキーを削除します。キーが`rgt`にのみ存在する場合はスキップします。
    - "r"（replace）：`lft`の値を`rgt`の値に置き換えます。
    - ""（コマンドなし、デフォルト）：辞書の場合は再帰的にマージします（"a"と同じ）。リストの場合は置き換えます（"r"と同じ）。その他の型の場合は置き換えます。
        lft (dict): マージされる左側（ベース）辞書。
        rgt (dict): マージする右側（ソース）辞書。キーには"!"の後にコマンドを含めることができます。
        dict: 右辞書の値がマージされた修正済みの左辞書。
        - コマンドなしのキー：「key」→ 辞書の場合は再帰的にマージ、その他の型は置き換え
        - コマンド付きキー：「key!a」→ 値を追加/拡張
        - コマンド付きキー：「key!r」→ 値を置き換え
        - コマンド付きキー：「key!d」→ キーを削除
    """
    if not lft:
        return rgt
    if not rgt:
        return lft

    dist = copy.deepcopy(lft)
    return _mergeDict(dist, rgt)


def _mergeDict(lft: dict, rgt: dict) -> dict:

    rgt_dic = {}
    for key in rgt.keys():
        if "!" in key:
            mkey, cmd = key.split("!", 1)
            rgt_dic[mkey] = (cmd, rgt[key])
        else:
            rgt_dic[key] = ("", rgt[key])

    for key in rgt_dic.keys():
        if key in lft:
            cmd = rgt_dic[key][0]
            val = rgt_dic[key][1]
            if isinstance(lft[key], dict) and isinstance(val, dict):
                if cmd in ("a", "append"):  # append
                    _mergeDict(lft[key], val)
                elif cmd in ("d", "delete"):  # delete
                    lft.pop(key, None)
                elif cmd in ("r", "replace"):  # replace
                    lft[key] = copy.deepcopy(val)
                else:  # append
                    _mergeDict(lft[key], val)
            elif isinstance(lft[key], list) and isinstance(val, list):
                if cmd in ("a", "append"):  # append
                    lft[key].extend(val)
                elif cmd in ("d", "delete"):  # delete
                    lft.pop(key, None)
                elif cmd in ("r", "replace"):  # replace
                    lft[key] = copy.deepcopy(val)
                else:  # replace
                    lft[key] = copy.deepcopy(val)
            else:
                lft[key] = copy.deepcopy(val)
        else:
            cmd = rgt_dic[key][0]
            val = rgt_dic[key][1]
            if cmd in ("d", "delete"):  # delete
                pass
            else:
                lft[key] = copy.deepcopy(val)
    return lft


def CompareDict(lft: dict, rgt: dict) -> bool:
    if lft.keys() != rgt.keys():
        return False
    for key in rgt:
        if key in lft:
            if isinstance(lft[key], dict) and isinstance(rgt[key], dict):
                if not CompareDict(lft[key], rgt[key]):
                    return False
            else:
                if lft[key] != rgt[key]:
                    return False
        else:
            return False
    return True

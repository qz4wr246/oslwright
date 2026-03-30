MSYS2 上で **GnuTLS をソースからビルドするための依存ライブラリのインストール手順と configure の流れ**を、実際に動く形でまとめてみるよ。MSYS2 は環境が複数（`msys` / `mingw64` / `mingw32` / `ucrt64`）あるので、**GnuTLS をどのターゲットでビルドするか**が重要なんだけど、ここでは一般的な **MINGW64（64bit）向けビルド**を例に説明するね。

---

# 🛠️ MSYS2 で GnuTLS をビルドする手順（MINGW64）

## 1. 🎯 まずは MSYS2 の更新
```sh
pacman -Syu
```
一度 MSYS2 を再起動して、もう一度：
```sh
pacman -Su
```

---

# 2. 📦 依存ライブラリのインストール

GnuTLS は依存が多いので、最低限必要なものをまとめると：

## 🔧 ビルドツール
```sh
pacman -S --needed \
  mingw-w64-x86_64-toolchain \
  autoconf automake libtool make \
  pkgconf
```

## 🔐 GnuTLS の主要依存
```sh
pacman -S --needed \
  mingw-w64-x86_64-nettle \
  mingw-w64-x86_64-gmp \
  mingw-w64-x86_64-libidn2 \
  mingw-w64-x86_64-libunistring \
  mingw-w64-x86_64-p11-kit \
  mingw-w64-x86_64-zlib \
  mingw-w64-x86_64-libtasn1
```

## 🔄（オプション）機能拡張
```sh
pacman -S --needed \
  mingw-w64-x86_64-guile \
  mingw-w64-x86_64-libseccomp \
  mingw-w64-x86_64-libev
```

---

# 3. 📁 ソースコードの取得
```sh
git clone https://gitlab.com/gnutls/gnutls.git
cd gnutls
```

---

# 4. ⚙️ configure の実行

MSYS2 では **必ず MINGW64 シェルで実行**してね（MSYS シェルではダメ）。

```sh
./bootstrap
```

次に configure：

```sh
./configure \
  --prefix=/mingw64 \
  --with-nettle \
  --with-included-libtasn1=no \
  --with-included-unistring=no
```

### よく使うオプション
| オプション | 説明 |
|-----------|------|
| `--prefix=/mingw64` | MINGW64 のパスにインストール |
| `--with-nettle` | 暗号バックエンドに Nettle を使用 |
| `--disable-guile` | Guile を使わない場合 |
| `--disable-doc` | ドキュメント生成を省略 |

---

# 5. 🔨 ビルド & インストール

```sh
make -j$(nproc)
make install
```

---

# 6. ✔️ 動作確認

```sh
gnutls-cli --version
```

---

# 💡 補足：MSYS2 でよくあるトラブル

## ❗ configure が nettle を見つけられない
`pkg-config` が MINGW64 のものを使っているか確認：

```sh
which pkg-config
```

→ `/mingw64/bin/pkg-config` であるべき。

---

## ❗ libidn2 / libunistring が見つからない
MSYS2 のパッケージ名が `mingw-w64-x86_64-libidn2` などになっているので、MSYS 版（`libidn2`）を入れても意味がない。必ず MINGW 版を入れる。

---

# 必要ならもっと深掘りできるよ
- MinGW32 / UCRT64 でのビルド
- static ビルド（`--enable-static`）
- cross-compile
- MSYS2 の PKGBUILD を使ったビルド方法

どの方向に進めたいか教えてくれたら、さらに最適な手順を作れるよ。

MSYS2 で **GnuTLS を cross-compile して、最終的に MSVC（Visual Studio）でリンク可能なライブラリを作る**のは、実はかなりクセがあります。理由は：

- GnuTLS は **MinGW / GCC を前提**にしている部分が多い
- MSVC は POSIX API が弱く、GnuTLS の依存（nettle, gmp, libtasn1 など）がそのままではビルドできない
- MSYS2 のパッケージは **MSVC 用の import library（.lib）を生成しない**

とはいえ、方法はあります。
ここでは **実際に動く構成**を３つのアプローチに分けて整理するね。

---

# 🧭 アプローチの全体像

| 方法 | 難易度 | 特徴 |
|------|--------|------|
| **① MinGW で GnuTLS をビルド → MSVC 用 .lib を生成** | 中 | 一番現実的。DLL は MinGW で作り、MSVC でリンクするための import library を作る |
| **② GnuTLS を MSVC で完全ビルド（CMake）** | 高 | 公式は非推奨。依存ライブラリの MSVC 対応が必要 |
| **③ vcpkg を使う（MSVC 対応済み）** | 低 | 実は最も簡単。MSVC 用 GnuTLS がそのまま入る |

---

# 🎯 **結論：MSVC で使うなら vcpkg が最強**
もし「MSVC でリンクできればよい」なら、これが圧倒的に楽。

```sh
vcpkg install gnutls:x64-windows
```

Visual Studio では自動でリンクされるし、依存も全部 MSVC 用に揃う。
ただし「MSYS2 で cross-compile したい」という目的なら、以下の①が本題。

---

# ① MinGW で GnuTLS をビルド → MSVC 用 import library を作る

## 1. MSYS2 MINGW64 で依存をインストール
```sh
pacman -S --needed \
  mingw-w64-x86_64-toolchain \
  mingw-w64-x86_64-gnutls \
  mingw-w64-x86_64-nettle \
  mingw-w64-x86_64-gmp \
  mingw-w64-x86_64-libtasn1 \
  mingw-w64-x86_64-libidn2 \
  mingw-w64-x86_64-libunistring
```

## 2. GnuTLS を MinGW でビルド（DLL を作る）
```sh
./configure --prefix=/mingw64 --disable-static
make -j$(nproc)
make install
```

これで `/mingw64/bin/libgnutls-*.dll` ができる。

---

# 3. MSVC 用の import library（.lib）を作る

MSVC は `.dll` だけではリンクできず、`.lib` が必要。
MinGW の DLL から `.def` を抽出し、MSVC の `lib.exe` で `.lib` を作る。

## DLL から def を生成
```sh
gendef libgnutls-30.dll
```

## MSVC の lib.exe で import library を作成
（Developer Command Prompt for VS で実行）

```bat
lib /def:libgnutls-30.def /machine:x64 /out:gnutls.lib
```

これで **MSVC がリンク可能な gnutls.lib** ができる。

---

# 4. Visual Studio プロジェクトでリンク

- `gnutls.lib` を追加
- DLL を実行フォルダにコピー
- 依存 DLL（nettle, gmp, libtasn1 など）も同様に import library を作る必要あり

---

# ② GnuTLS を MSVC で完全ビルド（非推奨・難易度高）

GnuTLS は Autotools ベースで、MSVC ビルドは公式にサポートされていない。
CMake 対応も不完全で、依存ライブラリ（nettle, gmp）が MSVC 非対応。

**MSVC ネイティブビルドは現実的ではない**。

---

# ③ vcpkg を使う（MSVC で最も簡単）

```sh
vcpkg install gnutls:x64-windows
```

Visual Studio では自動で include / lib が設定される。

---

# 🔍 どの方法を選ぶべきか？

| 目的 | 最適解 |
|------|---------|
| **MSVC で使いたいだけ** | vcpkg |
| **MSYS2 でビルドした DLL を MSVC で使いたい** | MinGW → import library 作成 |
| **完全に MSVC でビルドしたい** | 非推奨（依存が MSVC 非対応） |

---

# 必要なら次を詳しく書けるよ
- MinGW DLL → MSVC import library を自動生成するスクリプト
- 依存 DLL（nettle, gmp, tasn1）の .lib 作成手順
- Visual Studio のプロジェクト設定例
- cross-compile のための configure オプション最適化

どの方向に進めたいか教えてくれたら、もっと深く案内できる。

ここからは **MSYS2（MinGW）で GnuTLS を cross-compile し、MSVC でリンク可能な DLL＋import library を作るための “configure 最適化”** にフォーカスしてまとめるね。
MSVC で使う前提だと、GnuTLS の configure は **MinGW 用に最適化しつつ、MSVC で扱いやすい DLL を作る**ことが重要になる。

---

# ⚙️ **GnuTLS cross-compile 用 configure 最適化（MSVC でリンクする前提）**

MSVC でリンクするには：

- **DLL を MinGW で作る**
- **MSVC 用 import library（.lib）を生成する**
- **依存 DLL も同様に扱う**

そのため、configure では以下の方針が必要：

---

# 🎯 **最適化方針**

### 1. **DLL を作る（static は MSVC で扱いにくい）**
→ `--disable-static --enable-shared`

### 2. **MSVC が扱えない機能を切る**
- Guile
- DANE
- seccomp
- unneeded features

### 3. **依存ライブラリは MinGW のものを使う**
- nettle
- gmp
- libtasn1
- libidn2
- libunistring

### 4. **Windows 用のパスを明示**
→ `--prefix=/mingw64`

---

# 🧩 **推奨 configure コマンド（MSVC でリンクする DLL 用）**

```sh
./configure \
  --host=x86_64-w64-mingw32 \
  --build=x86_64-w64-mingw32 \
  --prefix=/mingw64 \
  --disable-static \
  --enable-shared \
  --with-nettle \
  --with-included-libtasn1=no \
  --with-included-unistring=no \
  --disable-guile \
  --disable-doc \
  --disable-tests \
  --disable-dane \
  --disable-libdane \
  --disable-seccomp \
  --disable-hardware-acceleration
```

---

# 📝 **各オプションの意味（MSVC 連携に重要なものだけ）**

### ✔ `--host=x86_64-w64-mingw32`
MinGW64 用にクロスコンパイルする指定。
MSYS2 の MINGW64 シェルなら実質ネイティブ扱い。

### ✔ `--disable-static`
MSVC で static ライブラリは扱いにくいので DLL のみにする。

### ✔ `--enable-shared`
MSVC でリンクするための DLL を作る。

### ✔ `--with-nettle`
暗号バックエンドを nettle に固定（GnuTLS の標準）。

### ✔ `--disable-guile`
Guile は Windows でビルドが困難なので切る。

### ✔ `--disable-dane --disable-libdane`
DANE は依存が多く、MSVC で扱いにくい。

### ✔ `--disable-seccomp`
seccomp は Linux 専用。

### ✔ `--disable-doc`
ビルド時間短縮。

### ✔ `--disable-tests`
MSVC 用 DLL を作るだけなら不要。

---

# 🧱 **依存ライブラリも DLL＋import library 化が必要**

GnuTLS の DLL だけでは MSVC でリンクできない。
依存 DLL も同じ手順で `.lib` を作る必要がある：

- nettle
- hogweed
- gmp
- libtasn1
- libidn2
- libunistring

### DLL → def → lib の流れ（MSVC 側）

```sh
gendef libgnutls-30.dll
lib /def:libgnutls-30.def /machine:x64 /out:gnutls.lib
```

依存 DLL も同様に `.lib` を作る。

---

# 🧪 **MSVC でのリンク確認**

Visual Studio のプロジェクトで：

- gnutls.lib
- nettle.lib
- hogweed.lib
- gmp.lib
- libtasn1.lib
- libidn2.lib
- libunistring.lib

を追加し、DLL を実行フォルダに置けば動く。

---

# 🔍 さらに最適化できる項目

必要なら、次も最適化できる：

- `--disable-openssl-compatibility`
- `--disable-ssl3-support`
- `--disable-alpn`
- `--disable-psk`
- `--disable-srp`
- `--disable-ocsp`
- `--disable-crypto-api`（Windows CNG を使わない場合）

用途に合わせて最適化できるよ。

---

# 📌 次に案内できる内容

必要なら、以下も詳しく書ける：

- 依存 DLL（nettle, gmp など）の import library 自動生成スクリプト
- Visual Studio のプロジェクト設定例（include / lib / runtime）
- GnuTLS の最小構成ビルド（TLS クライアントのみ）
- UCRT64 / Clang64 での cross-compile 最適化

どこまで深掘りしたいか教えてくれたら、さらに最適化できるよ。


了解、ここは **MSVC でリンク可能な import library（.lib）を、MinGW でビルドした DLL から自動生成するスクリプト**をまとめておくね。
GnuTLS だけでなく、**nettle / hogweed / gmp / libtasn1 / libidn2 / libunistring** など、依存 DLL すべてに使えるようにしてある。

MSVC でリンクするには：

- MinGW で DLL をビルド
- DLL → `.def` → `.lib` を生成
- Visual Studio で `.lib` をリンク

という流れになる。

---

# 🧰 **MinGW DLL → MSVC import library 自動生成スクリプト（PowerShell）**

以下は **Windows PowerShell** で動くスクリプト。
MinGW の `gendef.exe` と MSVC の `lib.exe` を使う。

---

## 📄 **make-msvc-importlibs.ps1**

```powershell
param(
    [Parameter(Mandatory=$true)]
    [string]$DllDir,

    [Parameter(Mandatory=$true)]
    [string]$OutDir
)

# MinGW の gendef を探す
$gendef = "gendef.exe"
if (-not (Get-Command $gendef -ErrorAction SilentlyContinue)) {
    Write-Error "gendef.exe が見つかりません。MSYS2 MinGW64 のパスを PATH に追加してください。"
    exit 1
}

# MSVC の lib.exe を探す
$libexe = "lib.exe"
if (-not (Get-Command $libexe -ErrorAction SilentlyContinue)) {
    Write-Error "MSVC の Developer Command Prompt から実行してください（lib.exe が必要）。"
    exit 1
}

# 出力ディレクトリ作成
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

# DLL を列挙
$dlls = Get-ChildItem -Path $DllDir -Filter "*.dll"

foreach ($dll in $dlls) {
    $name = $dll.BaseName
    $def = Join-Path $OutDir "$name.def"
    $lib = Join-Path $OutDir "$name.lib"

    Write-Host "=== $name.dll → $name.lib を生成中 ==="

    # def 生成
    & $gendef $dll.FullName

    # def を出力ディレクトリへ移動
    Move-Item "$name.def" $def -Force

    # import library 生成
    & $libexe /def:$def /machine:x64 /out:$lib

    Write-Host "生成完了: $lib"
}

Write-Host "すべての import library が生成されました。"
```

---

# 🚀 **使い方**

### 1. MinGW で GnuTLS と依存 DLL をビルド（または MSYS2 のパッケージを使用）
例：
```
/mingw64/bin/libgnutls-30.dll
/mingw64/bin/libnettle-8.dll
/mingw64/bin/libhogweed-6.dll
/mingw64/bin/libgmp-10.dll
...
```

### 2. PowerShell で実行

```powershell
.\make-msvc-importlibs.ps1 `
    -DllDir "C:\msys64\mingw64\bin" `
    -OutDir "C:\msvc-libs"
```

### 3. 出力例

```
C:\msvc-libs\libgnutls-30.lib
C:\msvc-libs\libnettle-8.lib
C:\msvc-libs\libhogweed-6.lib
C:\msvc-libs\libgmp-10.lib
...
```

これら `.lib` を Visual Studio のプロジェクトに追加すれば、
MinGW で作った DLL を **MSVC からリンク可能**になる。

---

# 🧪 **Visual Studio 側の設定ポイント**

- C/C++ → Additional Include Directories
  → MSYS2 の include パス（例：`C:\msys64\mingw64\include`）

- Linker → Additional Library Directories
  → `C:\msvc-libs`

- Linker → Input → Additional Dependencies
  → `libgnutls-30.lib` など

- DLL は実行フォルダにコピー（PATH に入れても OK）

---

# 🔧 必要ならさらに作れるもの

- **依存 DLL も含めて一括コピーするスクリプト**
- **GnuTLS の最小構成 DLL を作る configure 最適化**
- **MSVC 用の CMake プロジェクトテンプレート**
- **UCRT64 / Clang64 用 cross-compile スクリプト**

どこまで自動化したいか教えてくれたら、もっと便利な形に仕上げるよ。

MSYS2 の **INSTALL.md** にも書かれている通り、GnuTLS をビルドするには **gmplib（GMP）と nettle** が必須依存です。
ここでは、あなたが今開いているページの内容   [gitlab.com](https://gitlab.com/gnutls/gnutls/-/blob/master/INSTALL.md?ref_type=heads) を踏まえつつ、**MSYS2 で gmplib / nettle を正しくインストールし、GnuTLS のビルドに使える状態にする方法**を整理しておくね。

---

# 🔧 MSYS2 で gmplib / nettle をインストールする方法

GnuTLS の INSTALL.md にも次のように書かれている：

- **gmplib**: big number arithmetic（大きな整数演算）に必要
- **nettle**: cryptographic algorithms（暗号アルゴリズム）に必要
  [gitlab.com](https://gitlab.com/gnutls/gnutls/-/blob/master/INSTALL.md?ref_type=heads)

MSYS2 では、これらは **MinGW パッケージとして提供されている**ので、最も簡単なのは pacman でインストールする方法。

---

# ✅ 1. MinGW64（MSVC 連携を想定するなら 64bit）でインストール

MSYS2 の **MINGW64 シェル**を開いて次を実行：

```sh
pacman -S --needed \
  mingw-w64-x86_64-gmp \
  mingw-w64-x86_64-nettle \
  mingw-w64-x86_64-hogweed
```

### 補足
- **hogweed** は nettle の上位レイヤーで、GnuTLS が必要とする
- これらはすべて DLL と import library（MinGW 用 .a）が入っている
- GnuTLS の configure は pkg-config を使って自動検出する

---

# 🔧 2. ソースからビルドしたい場合（INSTALL.md の手順）

あなたが開いている INSTALL.md にも nettle のビルド例がある：

```
cd nettle-<version>
./configure --prefix=/usr --disable-openssl --enable-shared
make
sudo make install
```
  [gitlab.com](https://gitlab.com/gnutls/gnutls/-/blob/master/INSTALL.md?ref_type=heads)

MSYS2 で MinGW 用にビルドする場合は、次のように変更する：

```sh
./configure \
  --host=x86_64-w64-mingw32 \
  --prefix=/mingw64 \
  --enable-shared \
  --disable-static \
  --disable-openssl
make -j$(nproc)
make install
```

### GMP も同様に：

```sh
./configure \
  --host=x86_64-w64-mingw32 \
  --prefix=/mingw64 \
  --enable-shared \
  --disable-static
make -j$(nproc)
make install
```

---

# 🔧 3. GnuTLS の configure が依存を見つけられない場合

MSYS2 の MINGW64 シェルで次を確認：

```sh
which pkg-config
```

→ `/mingw64/bin/pkg-config` であること。

さらに：

```sh
pkg-config --libs nettle
pkg-config --libs gmp
```

これでパスが出れば GnuTLS の configure は通る。

---

# 🔧 4. MSVC でリンクする場合（MinGW DLL → MSVC .lib）

GnuTLS を MSVC で使うには、MinGW でビルドした DLL から import library を作る必要がある。
依存 DLL（gmp, nettle, hogweed）も同様。

DLL → .def → .lib の流れ：

```sh
gendef libnettle-8.dll
lib /def:libnettle-8.def /machine:x64 /out:nettle.lib
```

GMP も同様：

```sh
gendef libgmp-10.dll
lib /def:libgmp-10.def /machine:x64 /out:gmp.lib
```

---

# 🔍 まとめ

| ライブラリ | MSYS2 パッケージ | GnuTLS での役割 |
|-----------|------------------|------------------|
| gmplib | mingw-w64-x86_64-gmp | 大きな整数演算（暗号の基礎） |
| nettle | mingw-w64-x86_64-nettle | 暗号アルゴリズム |
| hogweed | mingw-w64-x86_64-hogweed | nettle の上位レイヤー |

INSTALL.md の内容と完全に一致しているよ   [gitlab.com](https://gitlab.com/gnutls/gnutls/-/blob/master/INSTALL.md?ref_type=heads)。

---

必要なら次も案内できる：

- GnuTLS の configure 最適化（MSVC 連携向け）
- 依存 DLL すべての import library を自動生成するスクリプト
- Visual Studio プロジェクト設定（include / lib / runtime）
- GnuTLS の最小構成ビルド（TLS クライアントのみ）

どこまで進めたいか教えてくれたら続けるよ。

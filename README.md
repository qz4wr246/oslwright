<h1>OSLwright: A C/C++ Open Source Library Builder for Windows</h1>
<p>
  <img alt="Version" src="https://img.shields.io/badge/version-0.1.2-blue.svg?cacheSeconds=2592000" />
  <a href="#" target="_blank">
    <img alt="License: MIT" src="https://img.shields.io/badge/License-MIT_License-yellow.svg" />
    <img alt="Language: python" src="https://img.shields.io/badge/Language-Python-green.svg" />
        <img alt="OS: Windows" src="https://img.shields.io/badge/OS-Windows-orange.svg" />
  </a>
</p>

OSLwright は、C/C++オープンソースライブラリ・ビルダーです。
Windows向けのC/C++ネイティブ・ライブラリをスクラッチビルドします。
<p>
<img src="docs/building.png" width="50%" style="display: block; margin: auto;" />
</p>

> [!WARNING]
> ## 🚧 ！工事中！ 👷‍♀️
> ほとんどテストを実施していません。<br>
> 全てのパッケージのビルドが完了することを確認しました。ただしリリース版だけです。

# Features

* Windows向けにC/C++オープンソースライブラリをビルドします。
* GUIで簡単にパッケージのビルドが出来ます。
* いくつかパッケージはCMakeConfigを追加しています。pkg-configは相対パスへ変更済み
* 気まぐれで商業利用に制限の少ないライセンスのパッケージを収集しています。
* ソースファイルをダウンロードしてスクラッチ・ビルドするので、バージョン管理やソースの追跡が可能です。
* 特に理由がなければ、[__vcpkg__](https://learn.microsoft.com/ja-jp/vcpkg/get_started/overview) をお勧めします。

# Requirements

次のアプリケーションをインストールしてください。

* Python 3.12 or higher [https://www.python.org/downloads/](https://www.python.org/downloads/)
* Microsoft Visual Studio 2022 or higher [https://visualstudio.microsoft.com/ja/downloads/](https://visualstudio.microsoft.com/ja/downloads/)
* CMake 4.3 or higher [https://cmake.org/download/](https://cmake.org/download/)
* Git for Windows [https://gitforwindows.org/](https://gitforwindows.org/)
* Git Large File Storage [https://git-lfs.com/](https://git-lfs.com/)
* 7zip [https://www.7-zip.org/download.html](https://www.7-zip.org/download.html)

# Get start
1. Python, VisualStudioなどOSLwrightが依存するアプリケーションをインストールします。
1. OSLwrightを起動します。<br>python仮想環境が作成されOSLwrightが起動します。
   ```dos
   > launch-oslwright.bat
   ```
1. 追加ツールダイアログが表示された場合は「Install tools」ボタンを押してください。

1. ビルドする対象のパッケージを選択します。

   <img src="docs/select.png" width="50%" style="display: block; margin: auto;"/>

1. [Build all] を押すと、選択されたパッケージが順次ビルドされます。

    ビルド予定時刻はあくまで目安です。ビルド完了は予定時刻より前後します。

1. ビルドされたパッケージは、&lt;OSLwright ディレクトリ&gt;/dist/以下にインストールされます。

# How to use the packages
ビルドされたパッケージを使用するには、いくつかの方法があります。

## A. パッケージをアプリケーションの開発フォルダへコピーして使用する方法
開発メンバーで開発環境を共有する場合に適しています。

1. 使用したいパッケージフォルダを&lt;開発フォルダ&gt;/3rdparty以下にコピーする。
    ```dos
    > cd <workdir>
    > xcopy <OSLwright>\dist 3rdparty /E /H /C /I
    ```
1. &lt;OSLwright ディレクトリ&gt;の cmake フォルダを&lt;開発フォルダ&gt;へコピーする。
    ```dos
    > cd <workdir>
    > xcopy <OSLwright>\cmake cmake /E /H /C /I
    ```
1. CMakeLists.txt に oslwrite module をロードするコードを記述する
    ```cmake
    if(MSVC)
      if (NOT CMAKE_TOOLCHAIN_FILE)
        # oslwrite module load
        include(${CMAKE_SOURCE_DIR}/cmake/oslwright.cmake)
      endif()
      if(OSLW_FRAMEWORK_PATH)
        # oslwrite framework path
        set(CMAKE_PREFIX_PATH "${OSLW_FRAMEWORK_PATH}")
      endif()
    endif()
    ```
## B. CMAKE_TOOLCHAIN_FILEを設定してパッケージを使用する方法

1. CMakeLists.txtに、CMAKE_PREFIX_PATHの設定を記述する
    ```cmake
    if(OSLW_FRAMEWORK_PATH)
      # oslwrite framework path
      set(CMAKE_PREFIX_PATH "${OSLW_FRAMEWORK_PATH}")
    endif()
    ```
1. オプションにCMAKE_TOOLCHAIN_FILEを設定しcmake コマンドを実行する
    ```dos
    > cmake.exe -G "Visual Studio 17 2022" -A x64 -DCMAKE_TOOLCHAIN_FILE="<OSLwright>/cmake/oslwright.cmake" -S . -B .\build_64
    ```
# Functions
DLLが再帰的な依存関係を有する場合は、cmakeは参照先のDLLを発見できません。<br>
依存するDLLのコピーをサポートする関数を定義しました。

## oslw_copy_depdll
ターゲットに依存するDLLを\$&lt;TARGET_FILE_DIR:\${target}&gt;へコピーする
```cmake
oslw_copy_depdll(TARGET   <target>       target name
                 [PATH    <directories>] Semicolon-separated list of OSLW's package directories.
                 [EXCLUDE <dll-list>]    exclude dll list
                )
```
Example
```cmake
# copy external dlls to bindir.
oslw_copy_depdll(
  TARGET ${target_name}
)
```
## oslw_install_depdll
ターゲットに依存するDLLをインストールする
```cmake
oslw_install_depdll(TARGET      <target>       target name
                   [DESTINATION <dir>]         Specify the directory which files will be installed.
                   [COMPONENT   <component>]   Specify an installation component name.
                   [PATH        <directories>] Semicolon-separated list of OSLW's package directories.
                   [EXCLUDE     <dll-list>]    exclude dll list
                   )
```
Exmaple
```cmake
# install external dlls
oslw_install_depdll(
  TARGET ${target_name}
  DESTINATION bin
  COMPONENT Application
)
```
## oslw_find_depdll
DLLが依存するDLLのパスを検索する。
```cmake
oslw_find_depdll(<VARNAME>                variable is assigned the result.
                  DLLS     <dll paths>    Semicolon-separated list of DLLs path.
                  [PATH    <directories>] Semicolon-separated list of OSLW's package directories.
                  [EXCLUDE <dll-list>]    exclude dll list
                  [WORKDIR <directory>]   workinng directory
                 )
```
Exmaple
```cmake
# find dependent dlls and copy
set(PLUGINS_DLLS a.dll b.dll)
oslw_find_depdll(DEPENDENT_DLLS
                DLLS ${PLUGINS_DLLS}
                WORKDIR ${PLUGINS_PATH}
)
add_custom_command(TARGET ${target_name} POST_BUILD
                      COMMAND ${CMAKE_COMMAND} -E copy_if_different
                      ${DEPENDENT_DLLS}
                      "$<TARGET_FILE_DIR:${target_name}>"
                      COMMAND_EXPAND_LISTS)

```

# Note
OSLwrightは、各パッケージをリリースビルドしています。MSVCランタイムライブラリのコンパイルオプションはMultiThreadedDLL(/MD)に設定されます。<br>
開発するアプリケーションにおいて、MSVCランタイムライブラリのコンパイルオプションの設定は、リリース・デバックの両方ともにMultiThreadedDLL(/MD)へ変更してください。

# Troubleshooting

パッケージのビルドでエラーとなったときは、以下の項目を実施してください。

+ boost-1.90.0 はVisual Studio 2026を未サポート(2026/04)
+ logs/Output.log へログが出力されています。原因を確認してください。
+ packages/パッケージ/package.jsonc を確認してください。
+ sourcesディレクトリのパッケージ・ディレクトリを削除（ソースファイルが壊れている）
+ cacheディレクトリにパッケージ・アーカイブを削除
（パッケージ・アーカイブが壊れている）
+ optionsディレクトリのパッケージ・オプションファイルを削除（stageを最初のdownloadから実行したい）


# Appendix
## ファルダ命名規則(Folder naming conventions)
インストールされたパッケージのファルダ名は、次の命名規則に従います。
<br>
&lt;package&gt;-&lt;version&gt;[-&lt;arch&gt;][-&lt;vc-version&gt;][-&lt;vc-runtime&gt;][-&lt;cu-versoin&gt;][-static][-debug|-release]

  |Folder name|Mean|
  |----|----|
  |&lt;package&gt;-&lt;version&gt;-x64-vc145-md|A 64-bit build with either both release and debug configurations or release only, and either both shared and static libraries or shared libraries only.|
  |&lt;package&gt;-&lt;version&gt;-x64-vc145-md-cu124|with cuda|
  |&lt;package&gt;-&lt;version&gt;-x64-vc145-md-static|static library only|
  |&lt;package&gt;-&lt;version&gt;-x64-vc145-md-release|release only|
  |&lt;package&gt;-&lt;version&gt;-x64-vc145-md-debug|debug only|
  |&lt;package&gt;-&lt;version&gt;| header  only|


# License
OSLwright のライセンスは MIT License です。<br>
サンプルソースコードのライセンスは MIT License と CC0 1.0 Universal です。<br>
各パッケージは、それぞれのライセンスに従ってください。<br>
__本ソフトウェアおよび生成物について、作者は一切の責任を負いません。利用による結果はすべて利用者の責任とします。__

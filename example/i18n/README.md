# サンプルコード

本サンプルは、OSLwrightを使用したCMakeのサンプルコードです。<br>

## サンプルを利用してプロジェクトを作成
OSLwrightと独立した形でパッケージを利用します。

### プロジェクトの作成
1. プロジェクトフォルダ

    任意の場所でプロジェクトフォルダを作成します。<br>
    次に&lt;OSLW_ROOT_DIR&gt;/example/i18nフォルダの内容をプロジェクトフォルダへコピーします。
    特に以下のファイル・フォルダが必要です。

    * cmake フォルダ
    * tools フォルダ
    * configure.bat
    * build.bat
    * CMakeLists.txt

1. configure.bat の編集

    開発環境に合わせてconfigure.batのUser Settingsを編集します。<br>
    ```bat
    set VS_VERSION=2022
    set VS_EDITION=Community
    set "OSLW_ROOT_DIR=%SCRIPT_DIR%\..\.."
    ＠REM set "BUILD_DIR=%SCRIPT_DIR%\build_x64"
    set "INSTALL_DIR=%SCRIPT_DIR%\dist"
    @REM set "CMAKE_OPTIONS="
    ```

    また、set "OSLW_ROOT_DIR=XXXXX" をコメントアウトします。<br>
    OSLW_ROOT_DIRが未定義の場合は、example/i18n/cmake/oslwright.cmakeをインクルードするようになります。

1. パッケージの選択

    &lt;OSLW_ROOT_DIR&gt;/dist以下のパッケージから必要な分だけを3rdparty以下へコピーします。

1. CMakeLists.txtの編集

    CMakeLists.txtへプロジェクトをビルドするためのコードを記述してください。<br>
    以下のコードによって、3rdparty以下のパッケージの検索やOSLwrightのサポート関数が使用できるようになります。
    ```cmake
    if(MSVC)
        #---------------------------
        # Setup oslwright environment
        #---------------------------
        if (NOT CMAKE_TOOLCHAIN_FILE)
            # oslwrite module load
            include(${CMAKE_SOURCE_DIR}/cmake/oslwright.cmake)
        endif()
        if(OSLW_FRAMEWORK_PATH)
            set(CMAKE_PREFIX_PATH "${OSLW_FRAMEWORK_PATH}")
        endif()
    endif()
    ```

    デバック時でもリリース版のパッケージをリンクするので、MSVCランタイムライブラリのコンパイルオプションの設定は、リリース・デバックの両方ともにMultiThreadedDLL(/MD)へ変更してください。
    ```cmake
    # OSLWright's packages are built with the /MD (Multi-threaded DLL runtime) option. Applications must also be built with /MD, even for debug builds.
    set(MSVC_RUNTIME_LIBRARY "MultiThreadedDLL")
    ```
1. アプリケーションの開発

    サンプルコードを参考にして開発を行ってください。

### コンフィグレーション＆ビルド

1. コンフィグレーション

    cmakeを使用しプロジェクトをコンフィグレーションします。<br>
    configure.bat を実行します。
    ```dos
    DOS> configure.bat
    ```
1. ビルド

    ビルドは以下のいずれかの方法を使用します。

    A: Visual Studio を使用する

        1. build_64/ソリューションファイル(*.sln)をVisual Studioから開く

        2. ソリューションのビルドをする

    B: build.bat を使用する

    ```dos
    DOS> build.bat
    ```

## ライセンス
サンプルソースコードのライセンスは UNLICENSEです。<br>
各パッケージは、それぞれのライセンスに従ってください。

#ifdef _WIN32
#include "windows.h"
#endif
#include <locale>
#include <string>
#include <fstream>
#include <iostream>
#include <vector>
#include <filesystem>

#include <cxxopts.hpp>
#define FMT_HEADER_ONLY
#include <fmt/format.h>

#include <log4cplus/logger.h>
#include <log4cplus/configurator.h>
#include <log4cplus/initializer.h>
#include <log4cplus/loggingmacros.h>

#include <i18n/I18nUtils.h>
#include <i18n/MO.h>

#define __(_X) I18N::__(_X)

namespace fs = std::filesystem;

int main(int argc, char **argv)
{
    // ロケールをUTF-8にする
#ifdef _WIN32
    std::locale::global(std::locale(".UTF8"));
#else
    std::locale::global(std::locale("ja_JP.utf8"));
#endif
    // ログ初期化
    log4cplus::Initializer initializer;

    // .exe のパスを取得
#ifdef _WIN32
    char c_exec_path[MAX_PATH];
    ::GetModuleFileNameA(NULL, c_exec_path, MAX_PATH);
    fs::path exec_path = fs::path(c_exec_path);
#else
    fs::path exec_path = fs::canonical("/proc/self/exe");
#endif

    fs::path root_dir;
    if (exec_path.parent_path().filename() == "bin") { // インストール先
        root_dir = exec_path.parent_path().parent_path();
    }
    else { // デバッグ中
        root_dir = exec_path.parent_path().parent_path().parent_path();
    }
    fs::path etc_dir = root_dir / "etc";
    fs::path log_dir = root_dir / "logs";

    // i18n
    std::string mofile = (etc_dir / "i18n" / "ja.mo").generic_string();
    I18N::I18nUtils::getInstance()->addMO(mofile);

    // コマンドラインオプション
    cxxopts::Options options("app.exe", "Example application.");
    options.add_options()
        ("h,help", "Print usage")
        ("loglevel", "Set loglevel", cxxopts::value<std::string>()->default_value("INFO"))
        ("filenames", "The filename(s) to process", cxxopts::value<std::vector<std::string>>());
    options.parse_positional({"filenames"});

    auto result = options.parse(argc, argv);
    if (result.count("help")) {
      std::cout << options.help() << std::endl;
      exit(0);
    }
    std::vector<std::string> input_files;
    if (result.count("filenames")) {
        std::vector<std::string> input_files = result["filenames"].as<std::vector<std::string>>();
    }
    if (input_files.size()) {
        std::cout << "args[0]=" << input_files[0] << std::endl;
    }

    // ログ設定
    std::string loglevel = result["loglevel"].as<std::string>();
    std::string logprop_file = (etc_dir / "log4.ini").string();
    log4cplus::helpers::Properties logprop(logprop_file);

    logprop.setProperty("loglevel", loglevel);  // loglevel
    logprop.setProperty("outputdir", log_dir.string());  // outputdir

    log4cplus::PropertyConfigurator logconf(logprop,
        log4cplus::Logger::getDefaultHierarchy(),
        log4cplus::PropertyConfigurator::fShadowEnvironment);
    logconf.configure();

    // ログ出力
    log4cplus::Logger logger = log4cplus::Logger::getInstance("main");

    LOG4CPLUS_INFO(logger, "Japanese: 日本語");
    LOG4CPLUS_WARN(logger, "Hello, World!");

    // fmt
    fmt::print("これは{}{}です。\n", "赤い", "リンゴ");

    LOG4CPLUS_INFO(logger, fmt::format(fmt::runtime(__("This is {}.")),__("a pen")));

    return 0;
}

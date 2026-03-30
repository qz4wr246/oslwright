use strict;
use warnings;

my ($file, $root_dir_arg) = @ARGV;
die "Usage: perl fix_pcfile.pl <file> <PATH_TO_REPLACE>\n" unless $file;

# 置換後の文字列
my $replacement_str = '${prefix}/../../..';

# ファイル読み込み
local $/ = undef;
open my $fh, '<', $file or die "Cannot open $file: $!";
my $content = <$fh>;
close $fh;

# 1. prefix の処理
if ($content !~ s/^prefix=.*/prefix=\${pcfiledir}\/..\/../m) {
    $content = "prefix=\${pcfiledir}/../..\n" . $content;
}

# 2. 基本的な変数の固定化
$content =~ s/^exec_prefix=(?!\$\{prefix\}).*/exec_prefix=\${prefix}/m;
$content =~ s/^libdir=(?!\$\{prefix\}).*/libdir=\${prefix}\/lib/m;
$content =~ s/^includedir=(?!\$\{prefix\}).*/includedir=\${prefix}\/include/m;
$content =~ s/^sharedlibdir=(?!\$\{prefix\}).*/sharedlibdir=\${prefix}\/lib/m;


# 3. 指定されたパス ($root_dir_arg) を ${prefix}/.. に置換
if ($root_dir_arg) {
    $content =~ s/\Q$root_dir_arg\E/$replacement_str/g;
}

# 書き戻し
open my $out, '>', $file or die "Cannot write $file: $!";
print $out $content;
close $out;

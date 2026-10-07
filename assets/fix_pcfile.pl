#!/usr/bin/env perl
use strict;
use warnings;
use File::Find;
use File::Spec;
use File::Basename;
use Getopt::Long qw(:config pass_through);

# ==============================================================================
# 1. Command Line Arguments & Validation
# ==============================================================================

my $dry_run = 0;
GetOptions('dry-run' => \$dry_run);

if (@ARGV < 3) {
    print STDERR "Usage: perl $0 <pc_file_name_or_path> <absolute_rootdir_path> <package_dir_name> [--dry-run]\n";
    exit 1;
}

my ($pc_input_arg, $absolute_rootdir_path, $package_dir_name) = @ARGV;

$pc_input_arg          =~ s/\\/\//g;
$absolute_rootdir_path =~ s/\\/\//g;
$package_dir_name      =~ s/\\/\//g;

my $pc_file_name = basename($pc_input_arg);

$absolute_rootdir_path =~ s/\/+$//;
$package_dir_name      =~ s/\/+$//;

my $search_base_dir = "$absolute_rootdir_path/$package_dir_name";

if (!-d $search_base_dir) {
    print STDERR "Error: Directory '$search_base_dir' does not exist.\n";
    exit 1;
}

if ($dry_run) {
    print "=== DRY-RUN MODE ENABLED (No files will be modified) ===\n\n";
}

# ==============================================================================
# 2. Directory Recursive Search & File Processing
# ==============================================================================

my @target_files;
my $escaped_base = quotemeta($search_base_dir);
my $escaped_file = quotemeta($pc_file_name);

my $file_match_regex = qr/^$escaped_base\/.*\/pkgconfig\/$escaped_file$/i;

find({
    wanted => sub {
        my $current_path = $File::Find::name;
        $current_path =~ s/\\/\//g;
        if ($current_path =~ $file_match_regex) {
            push @target_files, $current_path;
        }
    },
    no_chdir => 1,
}, $search_base_dir);

if (!@target_files) {
    print "No matching '$pc_file_name' files found under specified directory structure ($search_base_dir).\n";
    exit 0;
}

foreach my $pc_file (@target_files) {
    process_pc_file($pc_file, $absolute_rootdir_path);
}

# ==============================================================================
# 3. Core Processing Logic
# ==============================================================================

sub process_pc_file {
    my ($file_path, $rootdir_path) = @_;

    my $dirname = dirname($file_path);
    my $fh;
    my @lines;
    my $original_prefix = '';
    my @new_lines;
    my @diffs;
    my $is_changed = 0;
    my $line_num = 0;

    my $orig_line;
    my $chomped_line;
    my $diff;
    my $out;

    # ファイルの全行を読み込み
    if (!open($fh, '<', $file_path)) {
        print STDERR "Error: Cannot open file for reading: $file_path ($!)\n";
        return;
    }
    @lines = <$fh>;
    close($fh);

    # ステップ1：ファイル全体から prefix=... の絶対パスを抽出
    foreach my $line (@lines) {
        if ($line =~ /^\s*prefix\s*=\s*(.+)$/) {
            $original_prefix = $1;
            $original_prefix =~ s/\s+$//;
            $original_prefix =~ s/\\/\//g;
            last;
        }
    }

    if (!$original_prefix || $original_prefix =~ /\$\{/) {
        $original_prefix = $search_base_dir;
    }

    # ステップ2：確定した original_prefix を用いて各行の書き換えを実行
    foreach my $line (@lines) {
        $line_num++;
        $orig_line = $line;
        chomp($orig_line);

        # 3.1. Rewrite 'prefix' line
        if ($line =~ /^(\s*prefix\s*=).+$/) {
            $line = "${1}\${pcfiledir}/../..\n";
        }
        # 3.2. 任意の『変数名=絶対パス』を判定して相対化
        elsif ($line =~ /^(\s*([a-zA-Z0-9_-]+)\s*=)\s*(.+)$/) {
            my $prefix_part = $1;
            my $var_name    = $2;
            my $var_val     = $3;
            $var_val =~ s/\\/\//g;

            if ($var_name ne 'prefix') {
                if (lc(substr($var_val, 0, length($original_prefix))) eq lc($original_prefix)) {
                    my $sub_path = substr($var_val, length($original_prefix));
                    $line = $prefix_part . "\${prefix}" . $sub_path . "\n";
                }
            }
        }
        # 3.3. 【強化】Libs, Cflags, Requires などを含む全メタデータ行内の絶対パスを相対化
        # 従来の「Libs:」「Cflags:」前方一致ルールを「フラグ行全般（コロンを含む行）」に拡張
        elsif ($line =~ /^[a-zA-Z0-9._-]+\s*:/) {
            # 正規表現を調整：以下の条件に合う“明示的な絶対パス”のみ置換する
            #  - ドライブレター形式 (C:/...) または先頭スラッシュ形式 (/...)
            #  - "/.." のような親ディレクトリ参照で始まるパスは除外
            #  - 変数参照 (${...}) や URL (http:// 等) を含むパスは除外
            # これにより URL や ${pcfiledir} を含む不正な置換を防ぐ
            # 前に非空白文字がない（先頭か空白の直後）ことを確認し、URL や ${...} を含むトークンは除外
            $line =~ s{(?<!\S)((?:-[a-zA-Z])?\s*)(([A-Za-z]:/|/)(?!\.\.)(?![^\s]*\$\{)(?![^\s]*http)[^\s]+)}{
                my $flag = $1;
                my $path = $2;
                # メタデータ行の絶対パスを ${libdir}/${includedir} に置換
                my $result_path = $path;
                if ($path =~ m{(?:/|\\)lib(?:/|\\|$)}i) {
                    # パス末尾に /lib があれば ${libdir} に置換
                    $result_path = '${libdir}';
                    # /lib/ より後ろがあればそれも含める
                    if ($path =~ m{(?:/|\\)lib(?:/|\\)(.+)$}i) {
                        $result_path .= '/' . $1;
                    }
                } elsif ($path =~ m{(?:/|\\)include(?:/|\\|$)}i) {
                    # パス末尾に /include があれば ${includedir} に置換
                    $result_path = '${includedir}';
                    # /include/ より後ろがあればそれも含める
                    if ($path =~ m{(?:/|\\)include(?:/|\\)(.+)$}i) {
                        $result_path .= '/' . $1;
                    }
                }
                $flag . $result_path;
            }egx;
        }

        push @new_lines, $line;

        $chomped_line = $line;
        chomp($chomped_line);
        if ($orig_line ne $chomped_line) {
            $is_changed = 1;
            push @diffs, { num => $line_num, before => $orig_line, after => $chomped_line };
        }
    }

    # 5. Output and Constraints Execution
    print "File: $file_path\n";
    if (!$is_changed) {
        print " -> No changes needed\n\n";
        return;
    }

    if ($dry_run) {
        print " -> Changes Preview:\n";
        foreach $diff (@diffs) {
            print "    Line $diff->{num}:\n";
            print "      [-] $diff->{before}\n";
            print "      [+] $diff->{after}\n";
        }
        print "\n";
    } else {
        if (!open($out, '>', $file_path)) {
            print STDERR "Error: Cannot open file for writing: $file_path ($!)\n";
            return;
        }
        print $out join('', @new_lines);
        close($out);
        print " -> Overwritten successfully\n\n";
    }
}

# ==============================================================================
# 4. Helper Functions: Path Processing & Relative Calculation
# ==============================================================================

sub replace_path_callback {
    my ($prefix_flag, $raw_path, $original_prefix, $absolute_rootdir_path, $dirname) = @_;

    my $norm_path = $raw_path;
    $norm_path =~ s{\\}{/}g;

    my $replacement = $raw_path;

    # ドライブレターを除去（パス正規化）
    my $norm_path_no_drive = $norm_path;
    $norm_path_no_drive =~ s{^[a-zA-Z]:}{};

    my $original_prefix_no_drive = $original_prefix;
    $original_prefix_no_drive =~ s{^[a-zA-Z]:}{};

    # Case A: 内部パス (original_prefix 配下) - ドライブレター除去版で照合
    if (lc(substr($norm_path_no_drive, 0, length($original_prefix_no_drive))) eq lc($original_prefix_no_drive)) {
        my $relative_part = substr($norm_path_no_drive, length($original_prefix_no_drive));
        $relative_part =~ s{^\/+}{};

        if ($relative_part =~ m{^lib(?:\/|$)}i) {
            $relative_part =~ s{^lib(?:\/|)}{};
            $replacement = "\${libdir}" . ($relative_part ne "" ? "/$relative_part" : "");
        }
        elsif ($relative_part =~ m{^include(?:\/|$)}i) {
            $relative_part =~ s{^include(?:\/|)}{};
            $replacement = "\${includedir}" . ($relative_part ne "" ? "/$relative_part" : "");
        }
        else {
            $replacement = "\${prefix}/" . $relative_part;
        }
    }
    # Case B: 外部パス (同じ rootdir の別プロジェクト、またはそれ以外の絶対パス)
    # 渡された $absolute_rootdir_path の配下にあれば、そこを起点として相対パスを計算
    elsif (lc(substr($norm_path_no_drive, 0, length($absolute_rootdir_path))) eq lc($absolute_rootdir_path)) {
        my $rel_path = calculate_relative_path($dirname, $norm_path);
        $replacement = "\${pcfiledir}/" . $rel_path;
    }
    # Case C: 今回の UCRT64（MSYS2）のように、全く異なる絶対パス空間を指している場合
    # ドライブレターが同じ、もしくはパスの相対化が可能な場合は $dirname からそのまま相対パスを生成
    else {
        my $rel_path = calculate_relative_path($dirname, $norm_path);
        $replacement = "\${pcfiledir}/" . $rel_path;
    }

    return $prefix_flag . $replacement;
}

sub calculate_relative_path {
    my ($from_dir, $to_path) = @_;

    $from_dir =~ s/^[a-zA-Z]://;
    $to_path   =~ s/^[a-zA-Z]://;

    my @from_parts = split(m{/}, $from_dir);
    my @to_parts   = split(m{/}, $to_path);

    if (@from_parts) {
        my $first_from = $from_parts[0];
        shift @from_parts if defined $first_from && $first_from eq '';
    }
    if (@to_parts) {
        my $first_to = $to_parts[0];
        shift @to_parts if defined $first_to && $first_to eq '';
    }

    my $common_index = 0;
    while ($common_index < @from_parts && $common_index < @to_parts) {
        my $from_segment = $from_parts[$common_index];
        my $to_segment   = $to_parts[$common_index];

        if (lc($from_segment) eq lc($to_segment)) {
            $common_index++;
        } else {
            last;
        }
    }

    my $up_count = @from_parts - $common_index;
    my @rel_parts;
    for (my $i = 0; $i < $up_count; $i++) {
        push @rel_parts, '..';
    }

    for (my $i = $common_index; $i < @to_parts; $i++) {
        push @rel_parts, $to_parts[$i];
    }

    return join('/', @rel_parts);
}

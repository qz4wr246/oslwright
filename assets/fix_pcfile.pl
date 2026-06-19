#!/usr/bin/env perl
use strict;
use warnings;
use File::Spec;
use File::Basename;
use File::Find;

# 1. Command Line Arguments Validation
if (@ARGV < 3) {
    print STDERR "Usage: perl $0 <pc_file_name> <absolute_rootdir_path> <package_dir_name> [--dry-run]\n";
    exit 1;
}

my ($target_pc_name, $rootdir, $package_dir, $dry_run_flag) = @ARGV;

# Check if dry-run mode is enabled
my $is_dry_run = 0;
if (defined $dry_run_flag && $dry_run_flag eq '--dry-run') {
    $is_dry_run = 1;
    print "=== DRY-RUN MODE ENABLED (No files will be modified) ===\n\n";
}

# Normalize target_pc_name (convert backslashes to forward slashes)
$target_pc_name =~ s/\\/\//g;

# Normalize paths to use forward slashes and eliminate duplicate slashes
$rootdir = File::Spec->rel2abs($rootdir);
$rootdir =~ s/\\/\//g;
$rootdir =~ s/\/+/\//g;
$rootdir =~ s/\/$//; # Remove trailing slash

$package_dir =~ s/\\/\//g;
$package_dir =~ s/\/+/\//g;
$package_dir =~ s/^\///; # Remove leading slash
$package_dir =~ s/\/$//; # Remove trailing slash

my $full_package_path = "$rootdir/$package_dir";

if (!-d $full_package_path) {
    print STDERR "Error: Target directory '$full_package_path' does not exist.\n";
    exit 1;
}

# 2. File Search Directory Structure
my @pc_files;
find(sub {
    my $current_file = $_;
    $current_file =~ s/\\/\//g; # Normalize current file name

    # Extract only the base name if target_pc_name contains a path
    my $target_base = basename($target_pc_name);

    if (-f $_ && lc($current_file) eq lc($target_base)) {
        my $dir = $File::Find::dir;
        $dir =~ s/\\/\//g;
        $dir =~ s/\/+/\//g;

        # Check if it matches the pattern: ${rootdir}/${package_dir}/*/pkgconfig/
        if ($dir =~ m/^\Q$full_package_path\E\/[^\/]+\/pkgconfig$/i) {
            push @pc_files, $File::Find::name;
        }
    }
}, $full_package_path);

if (!@pc_files) {
    print "No matching '$target_pc_name' files found under '$full_package_path/*/pkgconfig/'.\n";
    exit 0;
}

# Helper function to calculate relative path between two absolute paths
sub compute_relative_path {
    my ($from_dir, $to_dir) = @_;

    # Handle case-insensitivity for Windows drive letters (e.g., C:/ vs c:/)
    my @from_parts = split m{/}, $from_dir;
    my @to_parts   = split m{/}, $to_dir;

    shift @from_parts if @from_parts && $from_parts[0] eq '';
    shift @to_parts if @to_parts && $to_parts[0] eq '';

    # Safely find the common prefix using index-based loop to prevent syntax errors
    my $common_count = 0;
    while ($common_count < @from_parts && $common_count < @to_parts) {
        if (lc($from_parts[$common_count]) eq lc($to_parts[$common_count])) {
            $common_count++;
        } else {
            last;
        }
    }

    # Remove common parts
    splice(@from_parts, 0, $common_count);
    splice(@to_parts, 0, $common_count);

    my $ups = join('/', (('..') x scalar(@from_parts)));
    my $downs = join('/', @to_parts);

    my $rel = $ups;
    $rel .= '/' . $downs if $downs ne '';
    return $rel;
}

# Process each found .pc file
foreach my $pc_file (@pc_files) {
    $pc_file =~ s/\\/\//g;
    my $pcfiledir = dirname($pc_file);

    # Read the file content
    my $read_fh;
    if (!open($read_fh, '<', $pc_file)) {
        print STDERR "Warning: Could not open '$pc_file' for reading: $!\n";
        next;
    }
    my @lines = <$read_fh>;
    close($read_fh);

    my $original_prefix = undef;

    # First pass: Identify the original absolute prefix path
    foreach my $line (@lines) {
        if ($line =~ /^prefix\s*=\s*(.+)$/) {
            $original_prefix = $1;
            $original_prefix =~ s/\s+$//; # trim trailing whitespace
            $original_prefix =~ s/\\/\//g;
            $original_prefix =~ s/\/+/\//g;
            last;
        }
    }

    if (!defined $original_prefix) {
        print "Skipping '$pc_file': No 'prefix' variable defined.\n";
        next;
    }

    my @new_lines;
    my $changed = 0;
    my @preview_diffs;

    # Second pass: Rewrite variables and flags
    foreach my $line (@lines) {
        my $orig_line = $line;
        chomp $line;

        # 3. Rewriting 'prefix' line
        if ($line =~ /^prefix\s*=\s*(.+)$/) {
            my $new_val = "prefix=\${pcfiledir}/../..";
            if ($line ne $new_val) {
                $line = $new_val;
                $changed = 1;
            }
        }
        # 3. Rewriting Core Variables (exec_prefix, libdir, includedir)
        elsif ($line =~ /^(exec_prefix|libdir|includedir)\s*=\s*(.+)$/) {
            my $var_name = $1;
            my $var_val = $2;
            $var_val =~ s/\\/\//g;

            # Case-insensitive replacement for paths
            if ($var_val =~ s/^\Q$original_prefix\E/\${prefix}/i) {
                $line = "$var_name=$var_val";
                $changed = 1;
            }
        }
        # 4. Rewriting 'Libs:' and 'Cflags:'
        elsif ($line =~ /^(Libs|Cflags)\s*:\s*(.+)$/) {
            my $field_name = $1;
            my $field_val = $2;
            $field_val =~ s/\\/\//g;

            # Match flags or absolute paths (supporting Windows drive letters like C:/)
            $field_val =~ s{([=-][-ILeE])?(([a-zA-Z]:)?/[^\s]+)}{
                my $prefix_flag = $1 // '';
                my $abs_path = $2;
                $abs_path =~ s/\/+/\//g;

                my $replacement = $prefix_flag . $abs_path;

                # Internal: Path points inside the current project prefix
                if ($abs_path =~ m/^\Q$original_prefix\E(\/|$)/i) {
                    my $rest = substr($abs_path, length($original_prefix));

                    if ($rest eq '/lib') {
                        $replacement = $prefix_flag . '${libdir}';
                    } elsif ($rest eq '/include') {
                        $replacement = $prefix_flag . '${includedir}';
                    } else {
                        $replacement = $prefix_flag . '${prefix}' . $rest;
                    }
                }
                # External: Path points to external companion projects under the same rootdir
                elsif ($abs_path =~ m/^\Q$rootdir\E(\/|$)/i) {
                    my $rel_path = compute_relative_path($pcfiledir, $abs_path);
                    $replacement = $prefix_flag . '${pcfiledir}/' . $rel_path;
                }

                $replacement;
            }eg;

            $line = "$field_name: $field_val";
        }

        my $final_line = $line . "\n";
        push @new_lines, $final_line;

        if ($orig_line ne $final_line) {
            $changed = 1;
            my $clean_orig = $orig_line;
            $clean_orig =~ s/\r?\n$//;
            push @preview_diffs, "  - $clean_orig\n  + $line";
        }
    }

    # 5. Output Messages & Overwrite
    if ($changed) {
        if ($is_dry_run) {
            print "File to be updated: $pc_file\n";
            print join("\n", @preview_diffs), "\n\n";
        } else {
            my $write_fh;
            if (!open($write_fh, '>', $pc_file)) {
                print STDERR "Error: Could not open '$pc_file' for writing: $!\n";
                next;
            }
            print $write_fh @new_lines;
            close($write_fh);
            print "Successfully updated relative paths in: $pc_file\n";
        }
    } else {
        print "No changes needed for: $pc_file\n";
    }
}

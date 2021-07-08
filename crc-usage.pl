#!/usr/bin/env perl
use strict;
use warnings;
use POSIX;
use Term::Size;

# Print centered subroutine
sub print_centered {
    my ($string, $width, $char) = @_;
    my $width_of_string = length($string);
    my $adjusted = ceil($width / 2) - ceil($width_of_string / 2);
    if ($adjusted % 2 != 0) {
        $adjusted -= 1;
    }
    my $formatted = $char x $adjusted . " " . $string . " " . $char x $adjusted;
    if (length($formatted) < $width) {
        my $fix = $formatted . $char x ($width - length($formatted));
    }
    elsif (length($formatted) > $width) {
        $formatted = substr($formatted, 0, -(length($formatted) - $width));
    }
    return $formatted . "\n";
}

# Need the terminal size
my ($width, $height) = Term::Size::chars *STDOUT{IO};

# If the width isn't defined, set it to 70
# -> If it is too wide, set it to 70
if (not $width ) {
    $width = 70;
}
elsif ($width > 70) {
    $width = 70;
}

# Need a begin and end dates, choose the whole year
my $year = `date +%y`;
my $begin = "01/01/" . $year;
my $end = `date +%m/%d/%y`;

# Global account
my $account;

# If user provides an account use that, otherwise use the Slurm default account
my $num_args = $#ARGV + 1;
if ($num_args > 1) {
    # Not an acceptable number of arguments, die
    die "ERROR: Usage, crc-usage.pl [optional account]\n";
}
elsif ($num_args == 1) {
    # User provided an account, check it exists in slurm
    $account = `sacctmgr -n list account account=$ARGV[0] format=account%30`;
    chomp $account;
    $account =~ s/^\s+//;
    # If it exists, set it
    if (length($account) != 0) {
        $account = $ARGV[0];
    }
}
else {
    # Use default Slurm account
    use Env qw(USER);
    $account = `sacctmgr -n list user $USER format=defaultaccount%30`;
    chomp $account;
    $account =~ s/\s//g;
}

if (length($account) != 0) {
    my $output = `/ihome/crc/bank/crc_bank.py usage $account`;
    print($output);
}
else {
    print("Your group doesn't have an account according to Slurm\n");
}

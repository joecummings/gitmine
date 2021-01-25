[![Build Status](https://travis-ci.com/joecummings/gitmine.svg?branch=master)](https://travis-ci.com/joecummings/gitmine)

# gitmine

Stop getting buried under countless Github Issues and PRs. Organize, reference, and close with ease.

Based on the amazing work done by Github itself on [hub](https://github.com/github/hub) and [Github CLI](https://cli.github.com/) (release while we were working on this project. Well done, us).

#### Who is this for?

I work on a lot of projects across many repositories. It was a pain in the a$$ to keep track of all the Issues I was assigned and PRs I had to review. Some tools provided a quick way to see Issues from one repository, but I needed a quick way to view, organize and open from any of these projects, thus `gitmine` was born.

If you aren't a heavy user of Github or maybe only have one repository you focus on, this is probably more than you need.

## Usage

### Command Line Arguments
```
Usage: gitmine [OPTIONS] COMMAND [ARGS]...

  Simple command-line tool for querying assigned Issues and PR reviews from
  Github.

Options:
  -v, --verbose  Give more output. Option is additive, and can be used up to
                 three times.
  --help         Show this message and exit.

Commands:
  config  Set or Access Github Config information.
  get     Get assigned Github Issues and/or Github PRs.
  go      Open a browser page for the given repositiory / issue.
```

### Config

To use gitmine you will first need to generate a Personal Access Token. You can follow the instructions [here](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token)

```
gitmine config username ~git-username~
gitmine config token ~git-token~
```

Gitmine gives you the option to encrypt your credentials with the --encrypt option.

## Installation

#### From PyPi
```
pip install gitmine
```
#### From source
```
pip install 'git+https://github.com/joecummings/gitmine.git'
```

## Contributing

See [Contributing.md](Contributing.md)

## Common Errors and FAQ's

* Running ```gitmine get prs``` with the wrong username will not error but return nothing

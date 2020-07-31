# gitmine

Stop getting buried under countless Github Issues and PRs. Organize, reference, and close with ease.

Based on the amazing work done by Github themselves on [hub](https://github.com/github/hub).

## Usage

### Command Line Arguments
```
Usage: gitmine [OPTIONS] COMMAND [ARGS]...

  Simple CLI for querying assigned Issues and PR reviews from Github.

Options:
  --help  Show this message and exit.

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

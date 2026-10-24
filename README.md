## Welcome to GitHub Pages

You can use the [editor on GitHub](https://github.com/TFLQW/tflqw.github.io/edit/main/README.md) to maintain and preview the content for your website in Markdown files.

Whenever you commit to this repository, GitHub Pages will run [Jekyll](https://jekyllrb.com/) to rebuild the pages in your site, from the content in your Markdown files.

### Markdown

Markdown is a lightweight and easy-to-use syntax for styling your writing. It includes conventions for

```markdown
Syntax highlighted code block

# Header 1
## Header 2
### Header 3

- Bulleted
- List

1. Numbered
2. List

**Bold** and _Italic_ and `Code` text

[Link](url) and ![Image](src)
```

For more details see [Basic writing and formatting syntax](https://docs.github.com/en/github/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax).

### Jekyll Themes

Your Pages site will use the layout and styles from the Jekyll theme you have selected in your [repository settings](https://github.com/TFLQW/tflqw.github.io/settings/pages). The name of this theme is saved in the Jekyll `_config.yml` configuration file.

### Support or Contact

Having trouble with Pages? Check out our [documentation](https://docs.github.com/categories/github-pages-basics/) or [contact support](https://support.github.com/contact) and we’ll help you sort it out.

### Google Scholar citation counts

[P_by_year.html](./P_by_year.html) and [P_by_type.html](./P_by_type.html) show a
`Cited by N` text badge after each paper's *Cite* link. The numbers come from the
public Google Scholar profile
[`lNvHzJEAAAAJ`](https://scholar.google.com/citations?user=lNvHzJEAAAAJ) and are
refreshed daily at 08:00 (UTC+2) by the
[update-scholar-citations](./.github/workflows/update-scholar-citations.yml)
workflow, which runs
[update_scholar_citations.py](./.github/scripts/update_scholar_citations.py) and
commits the change when a count moves.

- Manual refresh: `python .github/scripts/update_scholar_citations.py`
- Manual run in CI: Actions → *Update Google Scholar citation counts* → *Run workflow*
- If Scholar is unreachable, or rejects the GitHub Actions runner with HTTP 403,
  the pages are left untouched and the next daily run retries automatically.

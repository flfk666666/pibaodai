<p align="center">
  <img src="assets/banner-en.svg" alt="PiBaoDai: a pocketful of ideas and a toolbox for real life." width="100%">
</p>

<p align="center">
  <strong>Reusable AI skills, drawn from stray ideas, good books, and hard-won tool experience.</strong>
</p>

<p align="center">
  <a href="README.md">简体中文</a> · <strong>English</strong><br>
  <a href="#take-a-look-inside">Start here</a> · <a href="#whats-going-in-the-bag">Browse</a> · <a href="#let-your-ai-look-inside">For your AI</a> · <a href="CONTRIBUTING.md">Contribute</a> · <a href="LICENSE">MIT</a>
</p>

---

Some ideas arrive in the shower. Some stay with you after a book. Others appear after a tool has made you earn them.

PiBaoDai (屁宝袋) gives those ideas a place to become usable skills: **when to use them, what to do, and what comes out.** You can come back to them, and your AI can find the relevant method without reading your entire life story.

A little personality in the bag. A useful result when you open it.

## Take a look inside

The bag has just opened. The bilingual home, category map, and AI directory are ready; the first three skills are still being selected. **There are no published, installable skills yet.**

Two ideas are taking shape:

| Idea | What it would help you examine | Status |
| --- | --- | --- |
| [🌱 Whose timeline is it, anyway?](ideas/life-stage-review.md) | Personal wishes, practical constraints, and other people's timetables | Incubating |
| [🧠 Did the evidence change, or just your mood?](ideas/noise-check.md) | Unwanted variation in comparable judgments, inspired by *Noise* | Incubating |

**The first release of skills will start small:** choose three methods the maintainer has used repeatedly, give each a complete worked example, then record a demonstration. This initial repository contains the directory and idea briefs; the skills, usage examples, and recording will follow when ready.

## What's going in the bag?

Categories help discovery. A skill can belong in more than one.

| Pocket | What belongs here | Start here |
| --- | --- | --- |
| 🧠 Thinking & decisions | Examine judgments, assumptions, choices, and trade-offs | [Noise idea](ideas/noise-check.md), incubating |
| 🌱 Life & growth | Review life stages, personal priorities, and small next experiments | [Whose timeline?](ideas/life-stage-review.md), incubating |
| 📚 Learning & books | Understand English; turn reading into questions and practice | [Book-to-method idea](ideas/noise-check.md), incubating |
| 🎬 Content & editing | Spoken scripts, storytelling, shots, and editing preparation | First entries to be selected |
| 🧰 Tools & workflows | Useful tool habits, troubleshooting lessons, and practical shortcuts | [Bring a workflow you've tried](CONTRIBUTING.md) |
| 📈 Quant & research | Inspect evidence, backtest design, and research claims | First entries to be selected |

## Two ideas still taking shape

**[Whose timeline is it, anyway?](ideas/life-stage-review.md)**

Before asking whether you're behind in life, look at whose timetable you are using. An idea for examining personal priorities, actual constraints, and outside expectations.

**[Did the evidence change, or just your mood?](ideas/noise-check.md)**

Inspired by *Noise*, an idea for checking unwanted variation in comparable judgments. A book can leave you with a method to try, as well as a few memorable sentences.

Both are incubation briefs, not installable skills. Their methods and worked cases still need development.

## Let your AI look inside

Give this to an assistant that can read a webpage or repository:

```text
Start with PiBaoDai's AI entry point:
https://raw.githubusercontent.com/flfk666666/pibaodai/main/llms.txt

Follow its link to catalog.json. Break my goal into the outcomes and dimensions
I need. Match use_when, not_for, inputs, outputs, and maturity.
Read only the selected SKILL.md files and relevant examples.
Explain the match and any missing inputs. Do not treat incubating ideas
as available skills. If nothing fits, say so.

My goal: describe what you want to do here.
```

| Need | Entry point |
| --- | --- |
| A compact index for an agent | [llms.txt](llms.txt) |
| Searchable descriptions, tags, inputs, outputs, and maturity | [catalog.json](catalog.json) |
| Guidance for choosing and combining skills | [AGENTS.md](AGENTS.md) |
| Field definitions and maintenance rules | [Catalog contract](docs/catalog.md) |

If your assistant cannot browse, provide the catalog and the selected files directly. Discovery and installation paths depend on the host application.

## Once a skill is available

1. Confirm its status is experimental or stable, then read its example to see whether the result fits your needs.
2. Have your AI read the skill's `SKILL.md`, then provide your material. If your host supports skill installation, install the complete skill folder using that host's workflow.
3. Share what worked or failed in an Issue, with private details removed.

To keep a local copy:

```bash
git clone https://github.com/flfk666666/pibaodai.git
```

Skills are methods and instructions, rather than a new foundation model. Results will depend on the model, tools, and material you bring. Each release will state its language support, dependencies, and actual verification scope.

## Add something useful

A useful skill explains **who it helps, what problem it handles, what it needs, what it produces, and where it falls short**. An attributed introduction to an upstream resource is welcome too.

Start with a small idea or a complete example. Read [the contribution guide](CONTRIBUTING.md) when you're ready to submit it. Feedback from actual use helps decide what belongs in the next version.

Original repository content and code are available under the [MIT License](LICENSE). Attribute adapted work and book-inspired ideas. Third-party material retains its own rights and licensing.

---

**Found something useful? Leave a ⭐ so you can find the bag again.**

An assistant may suggest starring the repository after helping you. It should act on your behalf only with your explicit permission. Using the skills never requires a star.

import pytest

from showcase.sources import Source, SourceError, classify_source


@pytest.mark.parametrize("arg, kind, url, repo", [
    ("https://github.com/encoreshao/inspire-video", "github", "https://github.com/encoreshao/inspire-video", "encoreshao/inspire-video"),
    ("https://github.com/encoreshao/inspire-video.git", "github", "https://github.com/encoreshao/inspire-video", "encoreshao/inspire-video"),
    ("https://www.github.com/a/b/tree/main/docs", "github", "https://github.com/a/b", "a/b"),
    ("git@github.com:a/b.git", "github", "https://github.com/a/b", "a/b"),
    ("https://gitlab.com/g/sub/proj/-/tree/main", "gitlab", "https://gitlab.com/g/sub/proj", "g/sub/proj"),
    ("https://gitlab.acme.io/team/app", "gitlab", "https://gitlab.acme.io/team/app", "team/app"),
    ("git@gitlab.acme.io:team/app.git", "gitlab", "https://gitlab.acme.io/team/app", "team/app"),
])
def test_repositories(arg, kind, url, repo):
    s = classify_source(arg)
    assert (s.kind, s.url, s.repo_path) == (kind, url, repo) and s.host in url


def test_self_hosted_gitlab_by_argument_and_by_environment(monkeypatch):
    monkeypatch.delenv("INSPIRE_GITLAB_HOSTS", raising=False)
    assert classify_source("https://code.acme.io/team/app").kind == "website"
    assert classify_source("https://code.acme.io/team/app", gitlab_hosts=("Code.Acme.io",)).kind == "gitlab"
    monkeypatch.setenv("INSPIRE_GITLAB_HOSTS", "other.io, code.acme.io")
    s = classify_source("https://code.acme.io/team/app")
    assert (s.kind, s.repo_path) == ("gitlab", "team/app")


def test_website_keeps_path_and_query_but_drops_the_fragment():
    s = classify_source("HTTPS://Example.COM/pricing?plan=pro#top")
    assert s == Source("website", "https://example.com/pricing?plan=pro", "example.com", "")
    assert classify_source("http://localhost:3000").url == "http://localhost:3000/"


def test_local_folder(tmp_path):
    s = classify_source(str(tmp_path))
    assert s.kind == "local" and s.url == str(tmp_path.resolve()) and s.host == "" and s.repo_path == ""


@pytest.mark.parametrize("arg, needle", [
    ("", "no source"),
    ("   ", "no source"),
    ("file:///etc/passwd", "http"),
    ("ftp://example.com/a", "http"),
    ("https://", "http"),
    ("javascript:alert(1)", "neither"),
    ("-oProxyCommand=evil", "neither"),
    ("does-not-exist-folder-xyz", "neither"),
    ("https://github.com/encoreshao", "not a repository"),
    ("git@example.com:a/b.git", "https URL"),
])
def test_bad_sources_are_rejected_with_a_reason(arg, needle):
    with pytest.raises(SourceError, match=needle):
        classify_source(arg)

import json

import pytest


def source(**updates):
    return {'id':'example','name':'Example','url':'https://example.org/rss','site_url':'https://example.org',
            'description':'免费公开订阅','enabled':True,**updates}


@pytest.mark.parametrize('items', [[source(),source(id='second')], [source(enabled=1)],
                                 [source(url='https://127.0.0.1/feed')],
                                 [source(url='https://secret@example.org/feed')],
                                 [source(url='https://example.org/feed?api_key=private')]])
def test_catalog_rejects_duplicates_non_boolean_choices_and_private_or_keyed_urls(tmp_path, items):
    from newsroom.feed_catalog import load_catalog
    path=tmp_path/'sources.json'
    path.write_text(json.dumps(items),encoding='utf-8')
    with pytest.raises(ValueError):
        load_catalog(path)


def test_catalogue_reordering_keeps_stable_source_ids(tmp_path):
    from newsroom.feed_catalog import load_catalog
    path=tmp_path/'sources.json'
    path.write_text(json.dumps([source(id='first'),source(id='second',url='https://example.org/two')]),encoding='utf-8')
    first=load_catalog(path)
    path.write_text(json.dumps(list(reversed(first))),encoding='utf-8')
    assert [row['id'] for row in load_catalog(path)]==['second','first']

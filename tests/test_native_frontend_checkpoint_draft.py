import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts import native_build as build
from scripts import verify_native_checkpoint_units as units
from scripts.native_checkpoint_contract import (
    BROWSER_TEST_SOURCE,
    validate_browser_contract,
)

ROOT = Path(__file__).resolve().parents[1]
NAME = 'upstream-156-frontend-r19'
DRAFT = ROOT / 'native/drafts' / NAME
BASE = ROOT / 'native/drafts/upstream-156-http-r18'


def read(path):
    return json.loads(path.read_bytes())


@pytest.fixture
def candidate():
    assert NAME in build.CANDIDATES
    return build.load_candidate(NAME)


def test_frontend_candidate_has_explicit_complete_native_dispatch():
    assert NAME in build.CANDIDATES
    assert units.PLAN_SPECS[NAME] == (136, 337)
    assert NAME in units.BROWSER_PLAN_CANDIDATES
    assert NAME in units.SOURCE_BOUND_BROWSER_CANDIDATES
    plan = units.load_plan(build.load_candidate(NAME))
    assert len(plan['binaries']) == 7
    assert sum(row['binary'] == 'browser_tests' for row in plan['cases']) == 21


def test_frontend_recipe_preserves_the_complete_registered_base(candidate):
    manifest = candidate['manifest']
    base = read(BASE / 'manifest.json')
    assert len(manifest['patches']) == 181
    assert manifest['patches'][:180] == base['patches']
    assert len(manifest['source_files']) == 353
    originals = {row['path']: row['sha256'] for row in manifest['source_files']}
    assert {row['path']: row['sha256'] for row in base['source_files']}.items() <= originals.items()
    extension = manifest['extension_batch']
    assert extension['base_candidate'] == 'upstream-156-http-r18'
    assert extension['base_manifest_sha256'] == hashlib.sha256((BASE / 'manifest.json').read_bytes()).hexdigest()
    assert extension['added_patches'] == len(extension['packets']) == 1
    for packet in extension['packets']:
        path = ROOT / packet['packet']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == packet['packet_sha256']
        observed = read(path)
        assert not any(observed[key] for key in ('compiled', 'native_executed', 'runtime_verified', 'production_admitted'))


def test_frontend_plan_accounts_for_every_normalized_source_declaration(candidate):
    plan = read(DRAFT / 'native-case-plan.json')
    expected = []
    for patch in candidate['manifest']['patches'][136:]:
        source = None
        added = {}
        for line in (DRAFT / 'patches' / patch['file']).read_text(encoding='utf-8-sig').splitlines():
            if line.startswith('diff --git a/'):
                source = line.split(' b/', 1)[1]
            elif source and line.startswith('+') and not line.startswith('+++'):
                added.setdefault(source, []).append(line[1:])
        for source, lines in added.items():
            for kind, fixture, case in units.CASE_PATTERN.findall('\n'.join(lines)):
                binary = ('components_unittests' if source.startswith('components/services/storage/')
                          else 'net_unittests' if source.startswith('net/')
                          else 'services_unittests' if source.startswith('services/network/')
                          else 'blink_unittests' if source.startswith('third_party/blink/')
                          else 'browser_tests' if source.startswith('chrome/')
                          else 'content_browsertests' if source.endswith('_browsertest.cc')
                          else 'content_unittests' if source.startswith('content/') else None)
                assert binary is not None
                expected.append({
                    'binary': binary, 'source': source, 'fixture': fixture,
                    'case': case, 'kind': kind, 'patch': patch['file'],
                })
    assert plan['cases'] == expected
    assert len(expected) == plan['native_case_bodies_prepared'] == 337
    assert expected[:337] == read(BASE / 'native-case-plan.json')['cases']
    assert plan['candidate_manifest_sha256'] == candidate['manifest_sha256']
    assert len({(row['binary'], row['fixture'], row['case']) for row in expected}) == 337
    assert sum(row['fixture'] == 'GlintHttpCookieSqlCheckpointTest' for row in expected) == 6
    assert sum(row['binary'] == 'browser_tests' for row in expected) == 21


def test_frontend_draft_does_not_admit_unexecuted_features(candidate):
    proof = read(DRAFT / 'preparation.json')
    assert proof['passed'] and proof['manifest_sha256'] == candidate['manifest_sha256']
    assert proof['git_index_forward_patches'] == proof['git_index_reverse_patches'] == 181
    assert proof['final_owned_sources_matched'] == 511 and proof['upstream_originals_restored'] == 353
    assert proof['native_bodies_prepared'] == 337 and proof['baseline_native_bodies_preserved'] == 337
    assert not any(proof[key] for key in ('public_registry_modified', 'canonical_source_modified',
                                        'cpp_typechecked', 'compiled', 'native_executed',
                                        'runtime_verified', 'production_admitted'))
    assert not any(candidate['manifest'][key] for key in ('compiled', 'runtime_verified', 'production_admitted'))


def test_frontend_browser_contract_matches_reconstructed_fixture(candidate, tmp_path):
    for patch in candidate['manifest']['patches']:
        path = DRAFT / 'patches' / patch['file']
        if ('diff --git a/' + BROWSER_TEST_SOURCE + ' ') not in path.read_text(encoding='utf-8-sig'):
            continue
        subprocess.run(['git', '-c', 'core.autocrlf=false', 'apply',
                        '--include=' + BROWSER_TEST_SOURCE, '--whitespace=error', str(path)],
                       cwd=tmp_path, check=True, capture_output=True, timeout=15)
    plan = read(DRAFT / 'native-case-plan.json')
    bindings = validate_browser_contract(tmp_path, plan)
    assert len(bindings) == 1
    assert plan['browser_execution']['forced_phase_is_gtest_pass'] is False
    assert plan['browser_execution']['maximum_crash_phase_seconds'] == 300
    changed = copy.deepcopy(plan)
    changed['browser_execution']['source_sha256'] = read(BASE / 'native-case-plan.json')['browser_execution']['source_sha256']
    with pytest.raises(ValueError, match='source hash'):
        validate_browser_contract(tmp_path, changed)


def test_frontend_receipt_distinguishes_typechecking_from_native_execution(candidate):
    proof = read(DRAFT / 'frontend-validation.json')
    assert proof['passed'] and proof['translation_units'] == 47
    assert proof['checkpoint_case_source_units'] == 30
    assert proof['native_declarations_prepared'] == 337
    assert len(proof['commands']) == 47
    assert all(row['returncode'] == 0 and not row['timed_out'] for row in proof['commands'])
    assert len({row['source'] for row in proof['commands']}) == 47
    assert proof['original_negative_control_reproduced']
    assert proof['input_postguards_passed']
    assert proof['shared_bindings_generated_without_variant_typemap']
    assert proof['upstream_blink_test_bindings_generated']
    assert not any(proof[key] for key in ('style_checks_disabled', 'linked',
                                        'native_executed', 'runtime_verified', 'production_admitted'))
    patch = candidate['manifest']['patches'][-1]
    assert proof['normalized_patch_sha256'] == patch['sha256']
    observation = read(DRAFT / 'packet-observations/0181.json')
    assert proof['corrected_source_sha256'] == observation['final_source_sha256']
    assert proof['source_correction_sha256'] == observation['original_patch_sha256']

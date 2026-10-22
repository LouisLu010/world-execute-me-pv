"""Publish an already built release bundle, verifying the remote tag and asset bytes.

Requires `gh auth login` and an explicitly pushed local Git tag. Creates a draft
pre-release, uploads attachments, checks SHA-256 digests, then publishes it.
Existing published releases are never modified by this helper.

python tools/publish_prerelease.py --tag v0.2.0-preview.1 --assets /path/to/bundle
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def run(*args,timeout=120):
    return subprocess.check_output(args,text=True,timeout=timeout).strip()


def api(path):
    return json.loads(run('gh','api',path))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag',required=True)
    parser.add_argument('--assets',type=Path,required=True)
    parser.add_argument('--repo',default='LouisLu010/world-execute-me-pv')
    args=parser.parse_args()
    commit=run('git','rev-parse',args.tag+'^{commit}')
    branch=api(f'repos/{args.repo}/branches/gpt-history-pv')['commit']['sha']
    assert commit==branch,(commit,branch,'tag must match the reviewed branch head')
    remote_ref=api(f'repos/{args.repo}/git/ref/tags/{args.tag}')['object']
    if remote_ref['type']=='tag':
        remote_commit=api(f'repos/{args.repo}/git/tags/{remote_ref["sha"]}')['object']['sha']
    else:remote_commit=remote_ref['sha']
    assert remote_commit==commit,(remote_commit,commit)
    checksums={}
    for line in (args.assets/'SHA256SUMS.txt').read_text().splitlines():
        sha,name=line.split('  ',1)
        path=args.assets/name
        with path.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        assert actual==sha,(name,'local checksum mismatch')
        checksums[name]=sha
    expected=set(checksums)|{'SHA256SUMS.txt'}
    assert {'same_process_v2_4k60.mp4','same_process_v2_1080p60.mp4'}<=expected
    notes=Path('docs/PRE_RELEASE.md').resolve()
    # Discovery is read-only. An existing published tag is an explicit stop condition.
    releases=api(f'repos/{args.repo}/releases?per_page=100')
    release=next((r for r in releases if r['tag_name']==args.tag),None)
    if release is not None:
        assert release['draft'],'Refusing to alter an already published release'
    else:
        print(run('gh','release','create',args.tag,'--repo',args.repo,'--verify-tag',
                  '--title','你还记得我吗？ / SAME PROCESS? — V2 Preview 1',
                  '--notes-file',str(notes),'--prerelease','--draft','--latest=false'),flush=True)
    for name in sorted(expected,key=lambda n: -(args.assets/n).stat().st_size):
        path=args.assets/name
        with path.open('rb') as f:want='sha256:'+hashlib.file_digest(f,'sha256').hexdigest()
        for attempt in range(3):
            release=api(f'repos/{args.repo}/releases/tags/{args.tag}')
            found=next((a for a in release['assets'] if a['name']==name),None)
            if found:
                assert found['state']=='uploaded' and found['size']==path.stat().st_size,found
                assert found.get('digest')==want,(name,found.get('digest'),want)
                print('VERIFIED UPLOAD '+name,flush=True)
                break
            try:
                run('gh','release','upload',args.tag,str(path),'--repo',args.repo,timeout=1800)
            except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as exc:
                print(f'Upload attempt {attempt+1} did not complete for {name}: {type(exc).__name__}',flush=True)
            # Verify on the next iteration; no overwrite or clobber is used.
        else:
            release=api(f'repos/{args.repo}/releases/tags/{args.tag}')
            found=next((a for a in release['assets'] if a['name']==name),None)
            assert found and found.get('digest')==want,(name,'upload failed')
    release=api(f'repos/{args.repo}/releases/tags/{args.tag}')
    assert expected=={a['name'] for a in release['assets']},'Unexpected or missing attachments'
    run('gh','release','edit',args.tag,'--repo',args.repo,'--draft=false','--prerelease','--latest=false')
    release=api(f'repos/{args.repo}/releases/tags/{args.tag}')
    assert not release['draft'] and release['prerelease']
    result={'url':release['html_url'],'repo':args.repo,'tag':args.tag,'commit':commit,
            'prerelease':True,'draft':False,'assets':[
                {k:a[k] for k in ['name','size','state','digest','browser_download_url']}
                for a in release['assets']]}
    # Keep publication receipt next to the bundle, outside the tagged source tree.
    (args.assets.parent/(args.tag+'-publication.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()

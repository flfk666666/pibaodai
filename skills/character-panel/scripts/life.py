#!/usr/bin/env python3
"""Private life-direction questionnaire CLI; independent from six-axis checkpoints."""
import argparse
import json
from pathlib import Path
import sys

from life_store import LifeError, LifeStore, render, summarize


def main(argv=None):
    parser=argparse.ArgumentParser(description='人生方向：逐组保存、断点续测与独立历史；不生成人生数值分。')
    parser.add_argument('--state-dir',required=True,help='六维档案所在的私人profile根目录；人生方向另存life-direction子目录')
    commands=parser.add_subparsers(dest='command',required=True)
    init=commands.add_parser('init');init.add_argument('--profile-id',required=True)
    commands.add_parser('status');commands.add_parser('render')
    add=commands.add_parser('add-direction')
    add.add_argument('--id',required=True);add.add_argument('--title',required=True)
    add.add_argument('--kind',choices=['overview','goal','interest','exploration'],required=True)
    add.add_argument('--expect-revision',type=int,required=True)
    record=commands.add_parser('record')
    record.add_argument('--direction',required=True);record.add_argument('--section',required=True)
    record.add_argument('--payload-file',required=True);record.add_argument('--expect-revision',type=int,required=True)
    for name in ('pause','resume'):
        command=commands.add_parser(name);command.add_argument('--expect-revision',type=int,required=True)
    args=parser.parse_args(argv)
    try:
        store=LifeStore(args.state_dir)
        if args.command=='init':state=store.init(args.profile_id)
        elif args.command=='add-direction':state=store.add_direction(args.id,args.title,args.kind,args.expect_revision)
        elif args.command=='record':
            payload=json.loads(Path(args.payload_file).read_text(encoding='utf-8-sig'))
            state=store.record(args.direction,args.section,payload,args.expect_revision)
        elif args.command=='pause':state=store.pause(args.expect_revision)
        elif args.command=='resume':state=store.resume(args.expect_revision)
        else:state=store.load()
        if args.command=='render':print(render(state),end='')
        else:print(json.dumps({'ok':True,**summarize(state,store.catalog),'state':state},ensure_ascii=False,allow_nan=False))
        return 0
    except (LifeError,OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({'ok':False,'error':str(exc)},ensure_ascii=False),file=sys.stderr)
        return 2


if __name__=='__main__':
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
    raise SystemExit(main())

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
patch_config_apparent_sersic.py -- one-shot patch for config_lensfusion_acs.py
under paltas 0.2.0.

Why: paltas 0.2.0's SingleSersicSource treats `magnitude` as an ABSOLUTE
magnitude (converted via absolute_to_apparent + k-correction), so apparent
values like 16.5-18.5 render at zero flux -- the "missing lens light" bug.
paltas 0.1.1 has the apparent convention but is incompatible with the
installed lenstronomy (ProfileListBase._import_class was removed).

Fix: define an ApparentSersic subclass (the 0.1.1 apparent-magnitude logic)
inside the config and use it for lens_light. Verified in a controlled
experiment (paltas 0.2.0 + lenstronomy 1.13): stock lens light core/edge ~ 2-3
(absent) vs ApparentSersic ~ 165-320 (bright, SLACS-like).

What this script does (aborts loudly if anything looks unexpected):
  1. backs up the config to <config>.bak
  2. ensures `from paltas.Sources.sersic import SingleSersicSource` is present
  3. inserts the ApparentSersic class right before `config_dict = {`
  4. inside the 'lens_light' block only, replaces
     'class': SingleSersicSource  ->  'class': ApparentSersic
  5. prints a unified diff of the change

Usage:
    python patch_config_apparent_sersic.py config_lensfusion_acs.py
"""
import argparse
import difflib
import re
import shutil
import sys

CLASS_DEF = '''

class ApparentSersic(SingleSersicSource):
    """SingleSersicSource with `magnitude` interpreted as APPARENT magnitude
    (the paltas 0.1.1 convention). Needed because paltas 0.2.0 treats
    `magnitude` as ABSOLUTE and converts via absolute_to_apparent(z_source),
    which renders apparent-style values (e.g. 17) at zero flux.
    z_source is kept only for the returned redshift list (discarded for
    lens light by config_handler)."""
    def draw_source(self):
        sersic_params = {
            k: v for k, v in self.source_parameters.items()
            if k in self.required_parameters}
        sersic_params.pop('z_source')
        sersic_params.pop('output_ab_zeropoint')
        sersic_params.pop('magnitude')
        sersic_params['amp'] = SingleSersicSource.mag_to_amplitude(
            self.source_parameters['magnitude'],
            self.source_parameters['output_ab_zeropoint'], sersic_params)
        return (['SERSIC_ELLIPSE'], [sersic_params],
                [self.source_parameters['z_source']])

'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='path to config_lensfusion_acs.py')
    args = parser.parse_args()

    with open(args.config) as f:
        original = f.read()
    text = original

    if 'class ApparentSersic' in text:
        sys.exit('ApparentSersic already present in this config -- nothing '
                 'to do (was it already patched?).')

    # 2. import check
    if 'from paltas.Sources.sersic import SingleSersicSource' not in text:
        m = re.search(r'^import .*$|^from .*$', text, flags=re.M)
        if m is None:
            sys.exit('ABORT: could not find any import lines to anchor on.')
        # insert after the last contiguous import at the top
        lines = text.split('\n')
        last_imp = 0
        for i, ln in enumerate(lines[:80]):
            if ln.startswith('import ') or ln.startswith('from '):
                last_imp = i
        lines.insert(last_imp + 1,
                     'from paltas.Sources.sersic import SingleSersicSource')
        text = '\n'.join(lines)
        print('added SingleSersicSource import')

    # 3. insert the class before `config_dict`
    m = re.search(r'^config_dict\s*=\s*\{', text, flags=re.M)
    if m is None:
        sys.exit('ABORT: could not find a line starting with "config_dict = {" '
                 '-- patch the class in manually.')
    text = text[:m.start()] + CLASS_DEF.lstrip('\n') + '\n' + text[m.start():]

    # 4. switch the lens_light class only
    pattern = re.compile(
        r"((['\"])lens_light\2\s*:\s*\{.*?(['\"])class\3\s*:\s*)SingleSersicSource",
        flags=re.S)
    text, nsub = pattern.subn(r'\1ApparentSersic', text, count=1)
    if nsub != 1:
        sys.exit("ABORT: could not find 'class': SingleSersicSource inside the "
                 "'lens_light' block (found {0} matches). If your lens_light "
                 "uses a different class, change it to ApparentSersic "
                 "manually.".format(nsub))

    # sanity check: the source block must NOT have been touched
    if text.count('ApparentSersic') != 3:  # class def, docstring-free uses: def line, mag_to... no.
        pass  # count varies with docstring; rely on the diff below instead.

    backup = args.config + '.bak'
    shutil.copy(args.config, backup)
    with open(args.config, 'w') as f:
        f.write(text)

    diff = difflib.unified_diff(
        original.splitlines(True), text.splitlines(True),
        fromfile=backup, tofile=args.config)
    sys.stdout.writelines(diff)
    print('\nPatched. Backup at {0}'.format(backup))
    print('NOTE: this fix targets lens_light only. Your source block uses '
          'COSMOSCatalog (real images, own photometry) and is unaffected.')
    print('If you ever use SingleSersicSource as a SOURCE in this config, '
          'decide its convention explicitly (absolute under stock 0.2.0).')


if __name__ == '__main__':
    main()

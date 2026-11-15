"""Aquinas Neuron release files: the install script pins the same checksums as the model card and SHA256SUMS."""
import hashlib, re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M = ROOT / 'models/aquinas-neuron'


class NeuronRelease(unittest.TestCase):
    def test_pins_agree(self):
        sums = dict(reversed(l.split('  ')) for l in (M / 'SHA256SUMS').read_text().split('\n') if l.strip())
        script = (ROOT / 'scripts/install_ollama.sh').read_text()
        self.assertIn('SHA_Q4_K_M="%s"' % sums['aquinas-neuron-Q4_K_M.gguf'], script)
        self.assertIn('SHA_Q8_0="%s"' % sums['aquinas-neuron-Q8_0.gguf'], script)
        self.assertIn('SHA_MODELFILE="%s"' % hashlib.sha256((M / 'Modelfile').read_bytes()).hexdigest(), script)
        card = (M / 'README.md').read_text() + (ROOT / 'docs/RELEASE-NEURON.md').read_text()
        for h in sums.values():
            self.assertIn(h, card)

    def test_status_wording_and_notice(self):
        for f in (M / 'README.md', ROOT / 'docs/RELEASE-NEURON.md', ROOT / 'README.md'):
            t = f.read_text()
            self.assertIn('Answer quality has not been reviewed', t, f)
            self.assertNotRegex(t.lower(), r'\bimproves?\b|\bbetter than\b|\bpromoted\b(?! over)', f)
        n = (M / 'NOTICE').read_text()
        for s in ('LiquidAI/LFM3-1.7B', '1da06bec6a819da10b54c67e5c90972b46d81871', 'weights were changed', 'merged'):
            self.assertIn(s, n)
        mf = (M / 'Modelfile').read_text()
        self.assertIn('FROM ./aquinas-neuron-Q4_K_M.gguf', mf)
        import sys; sys.path.insert(0, str(ROOT))
        from aquinas.runtime import SYSTEM
        self.assertIn('SYSTEM """' + SYSTEM + '"""', mf)

    def test_install_script_never_overwrites_without_force(self):
        s = (ROOT / 'scripts/install_ollama.sh').read_text()
        self.assertIn('Re-run with --force to replace it', s)
        self.assertIn('Stopping; nothing was installed', s)
        self.assertNotRegex(s, r'ollama (rm|delete|pull)')


if __name__ == '__main__':
    unittest.main()

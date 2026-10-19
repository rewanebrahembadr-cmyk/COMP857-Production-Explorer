# Validation of this package

Checked on 19 October 2026 with Python 3.12 and the direct dependencies pinned in `requirements.txt`.

- 16 automated tests passed: 12 numerical/model checks and four Streamlit AppTest interaction checks.
- The regression test checks all 267 bundled notebook cases for objective agreement and feasibility within an absolute tolerance of 1e-6.
- The model checks include the baseline dual signs, basis inverse, infeasibility limits, resource saturation, coefficient-boundary alternatives, minimum-C range and both joint-change examples.
- Interface checks navigate every page and exercise live slider changes, exact coefficient breakpoints, infeasible inputs and joint presets.
- A separately launched Streamlit server returned HTTP 200 with `ok` from its health endpoint.

These checks were performed locally. They do not mean a public Streamlit app has already been deployed. Browser layout and the final public link should be checked after deployment. Shared reference data and the original assignment still need to agree.

Re-run the checks after editing the model or dependencies:

```bash
python -m unittest discover -s tests -v
```

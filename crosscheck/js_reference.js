// Runs the ORIGINAL JS classifier and depth check (read-only, from the
// ves-interpretation-agent repo) on a JSON array of readings.
// Usage: node js_reference.js <agentDir> <inputs.json> <outputs.json>
const fs = require('fs')
const path = require('path')

const [agentDir, inPath, outPath] = process.argv.slice(2)
const {checkLabel} = require(path.resolve(agentDir, 'curveType.js'))
const {checkDepthArithmetic} = require(path.resolve(agentDir, 'depthArithmetic.js'))

const readings = JSON.parse(fs.readFileSync(inPath, 'utf8'))
const out = readings.map((r) => {
  const res = {}
  try {
    res.label = checkLabel(r)
  } catch (e) {
    res.label = {error: e.message}
  }
  try {
    const d = checkDepthArithmetic(r)
    delete d.note // fixed explanatory text, not part of the result
    res.depth = d
  } catch (e) {
    res.depth = {error: e.message}
  }
  return res
})
fs.writeFileSync(outPath, JSON.stringify(out))

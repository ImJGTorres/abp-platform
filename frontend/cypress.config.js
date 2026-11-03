import { defineConfig } from 'cypress'
import { execFileSync } from 'node:child_process'
import path from 'node:path'

const BACKEND = path.resolve('..', 'backend')
const PYTHON = process.env.PYTHON_BACKEND
  || path.join(BACKEND, 'venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')

// Ejecuta un comando de Python en backend/ y devuelve la última línea de su salida.
function python(args) {
  const salida = execFileSync(PYTHON, args, { cwd: BACKEND, encoding: 'utf8' })
  return salida.trim().split('\n').pop()
}

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:5173',
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx}',
    setupNodeEvents(on) {
      on('task', {
        // HU-043 (SCRUM-543): datos de demostración y lectura de cola_correo
        hu043Seed() {
          python(['manage.py', 'seed_hu043_demo'])
          return JSON.parse(python([path.resolve('cypress/support/hu043_cola.py'), 'datos']))
        },
        hu043Cola(asunto) {
          return JSON.parse(python([path.resolve('cypress/support/hu043_cola.py'), 'cola', asunto]))
        },
      })
    },
  },
})

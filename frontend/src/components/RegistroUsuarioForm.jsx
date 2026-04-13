import { useState } from "react";
import { useRegistroForm, ROLES } from "../hooks/useRegistroForm";

export default function RegistroUsuarioForm() {
    const {
        form,
        erroresCampo,
        errorGeneral,
        loading,
        exitoso,
        handleChange,
        handleSubmit,
        resetear,
    } = useRegistroForm();

    const [verContrasena, setVerContrasena] = useState(false);
    const [verConfirmar, setVerConfirmar] = useState(false);

    return (
        <div className="max-w-lg mx-auto bg-white rounded-xl border border-gray-200 p-8 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900 mb-1">Registrar usuario</h2>

            {/* Confirmación de éxito  */}
            {exitoso && (
                <div role="status"
                    className="mb-5 flex items-start gap-3 rounded-lg bg-green-50
                        border border-green-200 px-4 py-3">
                    <span className="mt-0.5 flex-shrink-0 w-5 h-5 rounded-full bg-green-500 flex items-center justify-center">
                        <svg className="w-3 h-3 text-white" viewBox="0 0 12 12" fill="none">
                            <polyline points="2,6 5,9 10,3" stroke="currentColor" strokeWidth="2"
                                strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </span>
                    <div className="flex-1">
                        <p className="text-sm font-medium text-green-800">
                            Usuario creado correctamente.
                        </p>
                        <p className="text-xs text-green-600 mt-0.5">
                            Puedes registrar otro usuario o cerrar este formulario.
                        </p>
                    </div>
                    <button onClick={resetear}
                        className="text-green-600 hover:text-green-800 text-xs font-medium whitespace-nowrap">
                        + Nuevo
                    </button>
                </div>
            )}

            {/*  Error general */}
            {errorGeneral && (
                <div role="alert"
                    className="mb-5 flex items-center gap-2 rounded-lg bg-red-50
                        border border-red-200 px-4 py-3">
                    <svg className="w-4 h-4 text-red-500 flex-shrink-0"
                        viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" clipRule="evenodd"
                            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 002 0V6a1 1 0 00-1-1z" />
                    </svg>
                    <p className="text-sm text-red-700">{errorGeneral}</p>
                </div>
            )}

            {/*Formulario */}
            <form onSubmit={handleSubmit} noValidate className="space-y-4">

                <div className="grid grid-cols-2 gap-3">
                    <Field label="Nombre" name="nombre" placeholder="Ana"
                        value={form.nombre} onChange={handleChange} error={erroresCampo.nombre} />
                    <Field label="Apellido" name="apellido" placeholder="López"
                        value={form.apellido} onChange={handleChange} error={erroresCampo.apellido} />
                </div>

                <Field label="Correo electrónico" name="correo" type="email"
                    placeholder="ana@ufps.edu.co"
                    value={form.correo} onChange={handleChange} error={erroresCampo.correo} />

                <Field label="Contraseña" name="contrasena"
                    type={verContrasena ? "text" : "password"}
                    placeholder="Mínimo 8 caracteres"
                    value={form.contrasena} onChange={handleChange} error={erroresCampo.contrasena}
                    rightElement={
                        <ToggleOjo ver={verContrasena} toggle={() => setVerContrasena((v) => !v)} />
                    } />

                <Field label="Confirmar contraseña" name="confirmarContrasena"
                    type={verConfirmar ? "text" : "password"}
                    placeholder="Repite la contraseña"
                    value={form.confirmarContrasena} onChange={handleChange}
                    error={erroresCampo.confirmarContrasena}
                    rightElement={
                        <ToggleOjo ver={verConfirmar} toggle={() => setVerConfirmar((v) => !v)} />
                    } />

                {/* Selector de rol */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Rol <span className="text-red-500">*</span>
                    </label>
                    <select
                        name="tipo_rol"
                        value={form.tipo_rol}
                        onChange={handleChange}
                        className={`w-full h-9 rounded-md border px-3 text-sm bg-white text-gray-900
                        focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-shadow
                        ${erroresCampo.tipo_rol
                                ? "border-red-400 bg-red-50 focus:ring-red-400"
                                : "border-gray-300"}`}
                    >
                        <option value="">Selecciona un rol</option>
                        {ROLES.map((r) => (
                            <option key={r.value} value={r.value}>{r.label}</option>
                        ))}
                    </select>
                    {erroresCampo.tipo_rol && <ErrorMsg mensaje={erroresCampo.tipo_rol} />}
                </div>

                <button
                    type="submit"
                    disabled={loading}
                    className="w-full mt-2 h-9 rounded-md bg-red-600 text-white text-sm font-medium hover:bg-red-700 active:scale-[0.98]
                    disabled:opacity-60 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
                >
                    {loading && (
                        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10"
                                stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor"
                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                    )}
                    {loading ? "Guardando…" : "Guardar usuario"}
                </button>
            </form>
        </div>
    );
}


function Field({ label, name, type = "text", placeholder, value, onChange, error, rightElement }) {
    return (
        <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
                {label} <span className="text-red-500">*</span>
            </label>
            <div className="relative">
                <input
                    type={type} name={name} value={value} onChange={onChange}
                    placeholder={placeholder}
                    className={`w-full h-9 rounded-md border px-3 text-sm text-gray-900 placeholder-gray-400 transition-shadow
                    focus:outline-none focus:ring-2 focus:ring-red-500
                    ${rightElement ? "pr-9" : ""}
                    ${error
                            ? "border-red-400 bg-red-50 focus:ring-red-400"
                            : "border-gray-300"}`}
                />
                {rightElement && (
                    <div className="absolute inset-y-0 right-0 flex items-center pr-2">
                        {rightElement}
                    </div>
                )}
            </div>
            {error && <ErrorMsg mensaje={error} />}
        </div>
    );
}

function ErrorMsg({ mensaje }) {
    return (
        <p role="alert" className="mt-1 text-xs text-red-600 flex items-center gap-1">
            <svg className="w-3 h-3 flex-shrink-0" viewBox="0 0 12 12" fill="currentColor">
                <path fillRule="evenodd" clipRule="evenodd"
                    d="M6 1a5 5 0 100 10A5 5 0 006 1zm0 4a.75.75 0 01.75.75v2a.75.75 0 01-1.5 0v-2A.75.75 0 016 5zm0-1.5a.75.75 0 100-1.5.75.75 0 000 1.5z" />
            </svg>
            {mensaje}
        </p>
    );
}

function ToggleOjo({ ver, toggle }) {
    return (
        <button type="button" onClick={toggle} tabIndex={-1}
            aria-label={ver ? "Ocultar contraseña" : "Mostrar contraseña"}
            className="text-gray-400 hover:text-gray-600 transition-colors">
            {ver ? (
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94" />
                    <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                </svg>
            ) : (
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                </svg>
            )}
        </button>
    );
}
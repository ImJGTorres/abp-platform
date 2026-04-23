import { useState } from "react";
import { usuariosApi } from "../services/api";

export default function CargaMasivaEstudiantes() {
    const [archivo, setArchivo] = useState(null);
    const [loading, setLoading] = useState(false);
    const [resultado, setResultado] = useState(null);
    const [error, setError] = useState("");

    const handleArchivo = (e) => {
        const file = e.target.files?.[0] ?? null;
        setArchivo(file);
        setResultado(null);
        setError("");
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!archivo) return;

        setLoading(true);
        setError("");
        setResultado(null);

        try {
            const data = await usuariosApi.cargaMasiva(archivo);
            setResultado(data);
        } catch (err) {
            if (err?.type === "network") {
                setError(err.message);
            } else if (err?.status === 403) {
                setError("No tienes permiso para realizar esta acción.");
            } else if (err?.status === 400) {
                setError(err.data?.detail ?? "Archivo inválido.");
            } else {
                setError(err?.data?.detail ?? "Error inesperado al procesar el archivo.");
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-lg mx-auto bg-white rounded-xl border border-gray-200 p-8 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900 mb-1">
                Carga masiva desde Excel
            </h2>
            <p className="text-xs text-gray-500 mb-4">
                Sube un archivo <strong>.xlsx</strong> con columnas:
                <span className="font-mono"> codigo_estudiante, nombre, apellido, correo</span>.
                Se registrarán como estudiantes con contraseña temporal{" "}
                <span className="font-mono">Abp&lt;codigo&gt;</span>.
            </p>

            {error && (
                <div role="alert" className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3">
                    <p className="text-sm text-red-700">{error}</p>
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Archivo Excel
                    </label>
                    <input
                        type="file"
                        accept=".xlsx"
                        onChange={handleArchivo}
                        className="block w-full text-sm text-gray-700
                            file:mr-3 file:py-2 file:px-4
                            file:rounded-md file:border-0
                            file:text-sm file:font-medium
                            file:bg-red-50 file:text-red-700
                            hover:file:bg-red-100"
                    />
                </div>

                <button
                    type="submit"
                    disabled={!archivo || loading}
                    className="w-full h-9 rounded-md bg-red-600 text-white text-sm font-medium
                        hover:bg-red-700 active:scale-[0.98]
                        disabled:opacity-60 disabled:cursor-not-allowed
                        transition-all flex items-center justify-center gap-2"
                >
                    {loading && (
                        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10"
                                stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor"
                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                    )}
                    {loading ? "Procesando…" : "Cargar estudiantes"}
                </button>
            </form>

            {resultado && (
                <div className="mt-6 space-y-3">
                    <div className="rounded-lg bg-green-50 border border-green-200 px-4 py-3">
                        <p className="text-sm font-medium text-green-800">
                            {resultado.creados} usuarios creados
                        </p>
                        {resultado.omitidos > 0 && (
                            <p className="text-sm text-yellow-700 mt-1">
                                ⚠️ {resultado.omitidos} omitidos
                            </p>
                        )}
                    </div>

                    {Array.isArray(resultado.errores) && resultado.errores.length > 0 && (
                        <div className="rounded-lg border border-gray-200 overflow-hidden">
                            <table className="w-full text-xs">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-3 py-2 text-left font-medium text-gray-600">Fila</th>
                                        <th className="px-3 py-2 text-left font-medium text-gray-600">Correo</th>
                                        <th className="px-3 py-2 text-left font-medium text-gray-600">Motivo</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {resultado.errores.map((err, i) => (
                                        <tr key={i} className="border-t border-gray-200">
                                            <td className="px-3 py-2 text-gray-700">{err.fila}</td>
                                            <td className="px-3 py-2 text-gray-700">{err.correo || "—"}</td>
                                            <td className="px-3 py-2 text-gray-700">{err.motivo}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

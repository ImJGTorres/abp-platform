import { useState } from "react";
import { usuariosApi } from "../services/api";

export const ROLES = [
    { value: "estudiante", label: "Estudiante" },
    { value: "docente", label: "Docente" },
    { value: "director", label: "Director" },
    { value: "lider_equipo", label: "Líder de Equipo" },   // ← faltaba en versión anterior
    { value: "administrador", label: "Administrador" },
];

const INITIAL_STATE = {
    nombre: "",
    apellido: "",
    correo: "",
    contrasena: "",
    confirmarContrasena: "",
    tipo_rol: "",
};

function validar(form) {
    const errores = {};

    // nombre — validate_nombre: min 2 caracteres
    if (!form.nombre.trim()) {
        errores.nombre = "El nombre es obligatorio.";
    } else if (form.nombre.trim().length < 2) {
        errores.nombre = "El nombre debe tener al menos 2 caracteres.";
    }

    // apellido — validate_apellido: min 2 caracteres
    if (!form.apellido.trim()) {
        errores.apellido = "El apellido es obligatorio.";
    } else if (form.apellido.trim().length < 2) {
        errores.apellido = "El apellido debe tener al menos 2 caracteres.";
    }

    // correo — EmailField + validate_correo unique
    if (!form.correo.trim()) {
        errores.correo = "El correo es obligatorio.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.correo)) {
        errores.correo = "Formato de correo inválido.";
    }

    // contrasena — CharField min_length=8
    if (!form.contrasena) {
        errores.contrasena = "La contraseña es obligatoria.";
    } else if (form.contrasena.length < 8) {
        errores.contrasena = "La contraseña debe tener al menos 8 caracteres.";
    }

    // confirmarContrasena — solo validación frontend, no llega al backend
    if (!form.confirmarContrasena) {
        errores.confirmarContrasena = "Confirma la contraseña.";
    } else if (form.contrasena !== form.confirmarContrasena) {
        errores.confirmarContrasena = "Las contraseñas no coinciden.";
    }

    if (!form.tipo_rol) {
        errores.tipo_rol = "Selecciona un rol.";
    } else if (!ROLES.map((r) => r.value).includes(form.tipo_rol)) {
        errores.tipo_rol = "Rol inválido.";
    }

    return errores;
}


const CAMPOS_SERIALIZADOR = [
    "nombre",
    "apellido",
    "correo",
    "contrasena",
    "tipo_rol",
];

function mapearErroresBackend(data) {
    const erroresCampo = {};
    let errorGeneral = "";

    for (const campo of CAMPOS_SERIALIZADOR) {
        if (data[campo]) {
            erroresCampo[campo] = Array.isArray(data[campo])
                ? data[campo][0]
                : data[campo];
        }
    }

    // Error general: detail (403, 401, 500) o non_field_errors
    if (data.detail) {
        errorGeneral = data.detail;
    } else if (Array.isArray(data.non_field_errors) && data.non_field_errors.length) {
        errorGeneral = data.non_field_errors[0];
    } else if (Object.keys(erroresCampo).length === 0) {
        // Respuesta inesperada sin campos conocidos
        errorGeneral = "Error al crear el usuario. Intenta de nuevo.";
    }

    return { erroresCampo, errorGeneral };
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useRegistroForm() {
    const [form, setForm] = useState(INITIAL_STATE);
    const [erroresCampo, setErroresCampo] = useState({});
    const [errorGeneral, setErrorGeneral] = useState("");
    const [loading, setLoading] = useState(false);
    const [exitoso, setExitoso] = useState(false);

    function handleChange(e) {
        const { name, value } = e.target;
        if ((name === 'nombre' || name === 'apellido') && !/^[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ\s]*$/.test(value)) return
        setForm((prev) => ({ ...prev, [name]: value }));
        // Limpiar error del campo al escribir
        if (erroresCampo[name]) {
            setErroresCampo((prev) => ({ ...prev, [name]: "" }));
        }
        setErrorGeneral("");
        setExitoso(false);
    }

    function resetear() {
        setForm(INITIAL_STATE);
        setErroresCampo({});
        setErrorGeneral("");
        setExitoso(false);
    }

    async function handleSubmit(e) {
        e.preventDefault();
        setExitoso(false);
        setErrorGeneral("");

        const erroresLocales = validar(form);
        if (Object.keys(erroresLocales).length > 0) {
            setErroresCampo(erroresLocales);
            return;
        }

        setLoading(true);
        setErroresCampo({});

        try {
            await usuariosApi.crear({
                nombre: form.nombre.trim(),
                apellido: form.apellido.trim(),
                correo: form.correo.trim().toLowerCase(),
                contrasena: form.contrasena,
                tipo_rol: form.tipo_rol,
            });

            // Éxito
            setExitoso(true);
            setForm(INITIAL_STATE);

        } catch (err) {
            //Manejo de errores

            // Error de red (backend caído, sin conexión)
            if (err.type === "network") {
                setErrorGeneral("No se pudo conectar con el servidor. Verifica tu conexión.");
                return;
            }

            // Error 403: endpoint aún con AllowAny → no debería ocurrir ahora,
            // pero cuando se agregue IsAdminUser será el caso principal
            if (err.status === 403) {
                setErrorGeneral("No tienes permisos para crear usuarios. Inicia sesión como administrador.");
                return;
            }

            // Error 400: errores de validación del serializer
            if (err.status === 400 && err.data) {
                const { erroresCampo: ec, errorGeneral: eg } = mapearErroresBackend(err.data);
                setErroresCampo(ec);
                setErrorGeneral(eg);
                return;
            }

            // Error 500 u otros inesperados
            setErrorGeneral("Error inesperado en el servidor. Intenta de nuevo más tarde.");

        } finally {
            setLoading(false);
        }
    }

    return {
        form,
        erroresCampo,
        errorGeneral,
        loading,
        exitoso,
        handleChange,
        handleSubmit,
        resetear,
    };
}

import { useState } from "react";
import { usuariosApi } from "../services/api";


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

    if (!form.nombre.trim())
        errores.nombre = "El nombre es obligatorio.";

    if (!form.apellido.trim())
        errores.apellido = "El apellido es obligatorio.";

    if (!form.correo.trim()) {
        errores.correo = "El correo es obligatorio.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.correo)) {
        errores.correo = "Formato de correo inválido.";
    }

    if (!form.contrasena) {
        errores.contrasena = "La contraseña es obligatoria.";
    } else if (form.contrasena.length < 8) {
        errores.contrasena = "Mínimo 8 caracteres.";
    }

    if (!form.confirmarContrasena) {
        errores.confirmarContrasena = "Confirma la contraseña.";
    } else if (form.contrasena !== form.confirmarContrasena) {
        errores.confirmarContrasena = "Las contraseñas no coinciden.";
    }

    if (!form.tipo_rol)
        errores.tipo_rol = "Selecciona un rol.";

    return errores;
}


const CAMPOS_BACKEND = ["nombre", "apellido", "correo", "contrasena", "tipo_rol"];

function mapearErroresBackend(data) {
    const erroresCampo = {};
    let errorGeneral = "";

    for (const campo of CAMPOS_BACKEND) {
        if (data[campo]) {
            erroresCampo[campo] = Array.isArray(data[campo])
                ? data[campo][0]
                : data[campo];
        }
    }

    if (data.detail) {
        errorGeneral = data.detail;
    } else if (data.non_field_errors?.length) {
        errorGeneral = data.non_field_errors[0];
    } else if (Object.keys(erroresCampo).length === 0) {
        errorGeneral = "Error al crear el usuario. Intenta de nuevo.";
    }

    return { erroresCampo, errorGeneral };
}


export function useRegistroForm() {
    const [form, setForm] = useState(INITIAL_STATE);
    const [erroresCampo, setErroresCampo] = useState({});
    const [errorGeneral, setErrorGeneral] = useState("");
    const [loading, setLoading] = useState(false);
    const [exitoso, setExitoso] = useState(false);

    function handleChange(e) {
        const { name, value } = e.target;
        setForm((prev) => ({ ...prev, [name]: value }));
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

            setExitoso(true);
            setForm(INITIAL_STATE);
        } catch (err) {

            const data = err?.data ?? {};
            const { erroresCampo: ec, errorGeneral: eg } = mapearErroresBackend(data);
            setErroresCampo(ec);
            setErrorGeneral(eg);
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
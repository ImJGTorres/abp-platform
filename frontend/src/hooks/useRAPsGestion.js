import { useState, useEffect, useCallback } from 'react'
import { proyectosApi } from '../services/docenteApi'

/**
 * Hook personalizado para gestionar los Resultados de Aprendizaje del Proyecto (RAPs).
 *
 * Centraliza toda la lógica de estado y las operaciones asíncronas de CRUD para
 * que el componente RAPsProyecto solo se ocupe de renderizar la interfaz.
 *
 * @param {string|number} proyectoId - ID del proyecto cuyos RAPs se gestionan.
 *
 * @returns {{
 *   raps: Array<object>,
 *   loading: boolean,
 *   modalRAP: boolean,
 *   rapEditando: object|null,
 *   eliminando: number|null,
 *   confirmarEliminar: number|null,
 *   totalPorcentaje: number,
 *   porcentajeRestante: number,
 *   abrirCrear: Function,
 *   abrirEditar: Function,
 *   cerrarModal: Function,
 *   handleGuardarRAP: Function,
 *   pedirConfirmarEliminar: Function,
 *   cancelarEliminar: Function,
 *   ejecutarEliminar: Function,
 * }}
 */
export function useRAPsGestion(proyectoId) {
    const [raps, setRaps] = useState([])
    const [loading, setLoading] = useState(true)
    const [modalRAP, setModalRAP] = useState(false)
    const [rapEditando, setRapEditando] = useState(null)
    const [eliminando, setEliminando] = useState(null)
    const [confirmarEliminar, setConfirmarEliminar] = useState(null)

    // -----------------------------------------------------------------------
    // Carga de datos
    // -----------------------------------------------------------------------

    /** Obtiene la lista actualizada de RAPs desde la API. */
    const cargarRAPs = useCallback(async () => {
        setLoading(true)
        try {
            const data = await proyectosApi.listarRAPs(proyectoId)
            setRaps(data.results ?? data)
        } catch (err) {
            console.error('Error cargando RAPs:', err)
            setRaps([])
        } finally {
            setLoading(false)
        }
    }, [proyectoId])

    useEffect(() => {
        cargarRAPs()
    }, [cargarRAPs])

    // -----------------------------------------------------------------------
    // Operaciones de modal
    // -----------------------------------------------------------------------

    /** Abre el modal en modo creación. */
    const abrirCrear = useCallback(() => {
        setRapEditando(null)
        setModalRAP(true)
    }, [])

    /**
     * Abre el modal en modo edición con el RAP seleccionado.
     *
     * @param {object} rap - RAP a editar.
     */
    const abrirEditar = useCallback((rap) => {
        setRapEditando(rap)
        setModalRAP(true)
    }, [])

    /** Cierra el modal de creación/edición y limpia el estado de edición. */
    const cerrarModal = useCallback(() => {
        setModalRAP(false)
        setRapEditando(null)
    }, [])

    // -----------------------------------------------------------------------
    // Guardar (crear o editar)
    // -----------------------------------------------------------------------

    /**
     * Crea o actualiza un RAP según si hay un `rapEditando` activo.
     *
     * @param {object} formData - Datos del formulario del RAP.
     * @throws {Error} Si la llamada a la API falla (la propagación permite que
     *                 el modal muestre el error al usuario).
     */
    const handleGuardarRAP = useCallback(async (formData) => {
        try {
            if (rapEditando) {
                await proyectosApi.editarRAP(proyectoId, rapEditando.id, {
                    nombre: formData.nombre,
                    descripcion: formData.descripcion,
                    competencia_asociada: formData.competencia_asociada || null,
                    porcentaje_evaluacion: parseFloat(formData.porcentaje_evaluacion),
                })
            } else {
                await proyectosApi.crearRAP(proyectoId, {
                    nombre: formData.nombre,
                    descripcion: formData.descripcion,
                    competencia_asociada: formData.competencia_asociada || null,
                    porcentaje_evaluacion: parseFloat(formData.porcentaje_evaluacion),
                    orden: raps.length + 1,
                })
            }
            cerrarModal()
            cargarRAPs()
        } catch (err) {
            console.error('Error guardando RAP:', err)
            throw err
        }
    }, [proyectoId, rapEditando, raps.length, cerrarModal, cargarRAPs])

    // -----------------------------------------------------------------------
    // Eliminar
    // -----------------------------------------------------------------------

    /**
     * Solicita confirmación para eliminar un RAP.
     *
     * @param {number} id - ID del RAP a eliminar.
     */
    const pedirConfirmarEliminar = useCallback((id) => {
        setConfirmarEliminar(id)
    }, [])

    /** Cancela la confirmación de eliminación sin realizar ninguna acción. */
    const cancelarEliminar = useCallback(() => {
        setConfirmarEliminar(null)
    }, [])

    /**
     * Elimina definitivamente el RAP confirmado y recarga la lista.
     *
     * @param {number} id - ID del RAP a eliminar.
     */
    const ejecutarEliminar = useCallback(async (id) => {
        setConfirmarEliminar(null)
        setEliminando(id)
        try {
            await proyectosApi.eliminarRAP(proyectoId, id)
            cargarRAPs()
        } catch (err) {
            console.error('Error eliminando RAP:', err)
        } finally {
            setEliminando(null)
        }
    }, [proyectoId, cargarRAPs])

    // -----------------------------------------------------------------------
    // Valores computados
    // -----------------------------------------------------------------------

    /** Suma total de porcentajes de todos los RAPs del proyecto (0-100+). */
    const totalPorcentaje = raps.reduce((sum, r) => sum + (r.porcentaje_evaluacion ?? 0), 0)

    /** Porcentaje disponible para asignar a nuevos RAPs. */
    const porcentajeRestante = 100 - totalPorcentaje

    return {
        // Estado
        raps,
        loading,
        modalRAP,
        rapEditando,
        eliminando,
        confirmarEliminar,
        // Computados
        totalPorcentaje,
        porcentajeRestante,
        // Acciones de modal
        abrirCrear,
        abrirEditar,
        cerrarModal,
        // Acciones de datos
        handleGuardarRAP,
        pedirConfirmarEliminar,
        cancelarEliminar,
        ejecutarEliminar,
    }
}

import io
import json
import time
import oci
from fdk import response


def handler(ctx, data: io.BytesIO = None):
    try:
        body = json.loads(data.getvalue())
    except Exception:
        return response.Response(
            ctx, status_code=400,
            response_data=json.dumps({"error": "JSON inválido"})
        )

    pedido_id = body.get("pedido_id")
    estado = body.get("estado")
    rappi_order_id = body.get("rappi_order_id")

    if not pedido_id or not estado:
        return response.Response(
            ctx, status_code=400,
            response_data=json.dumps({"error": "Faltan campos obligatorios (pedido_id, estado)"})
        )

    try:
        signer = oci.auth.signers.get_resource_principals_signer()
        client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
        namespace = client.get_namespace().data
        bucket_name = "rappi-pedidos-estado"

        contenido = {
            "rappi_order_id": rappi_order_id,
            "pedido_id": pedido_id,
            "estado": estado,
            "actualizado_en": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        client.put_object(
            namespace_name=namespace,
            bucket_name=bucket_name,
            object_name=f"{pedido_id}.json",
            put_object_body=json.dumps(contenido)
        )
    except Exception as e:
        return response.Response(
            ctx, status_code=500,
            response_data=json.dumps({"error": f"No se pudo persistir el estado: {str(e)}"})
        )

    return response.Response(
        ctx, status_code=200,
        response_data=json.dumps({"ok": True, "pedido_id": pedido_id, "estado": estado})
    )
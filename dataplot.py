import math
import os
import shutil
import shapefile
import ezdxf

punti_cerchio_massimi = {
    1: 60,
    2: 30,
    3: 20,
    4: 15,
    5: 12,
    6: 10,
    7: 9,
    8: 8,
    9: 7
}


def coordinate_spicchio(x0, y0, spicchi, numero, raggio):
    # spicchi pieni
    punti_cerchio = punti_cerchio_massimi[spicchi] * spicchi
    k = 2 * math.pi / punti_cerchio
    inizio = int(punti_cerchio / spicchi) * numero
    fine = int(punti_cerchio / spicchi) * (numero + 1)
    if spicchi == 1:
        return [
            (
                x0 + math.cos(k * x) * raggio,
                y0 + math.sin(k * x) * raggio
            ) for x in range(inizio, fine + 1)]
    else:
        return [(x0, y0)] + [
            (
                x0 + math.cos(k * x) * raggio,
                y0 + math.sin(k * x) * raggio
            ) for x in range(inizio, fine + 1)] + [
                   (x0, y0)
               ]


def coordinate_cerchio(x0, y0, spicchi, raggio):
    punti_cerchio = punti_cerchio_massimi[spicchi] * spicchi
    k = 2 * math.pi / punti_cerchio
    return [
        (
            x0 + math.cos(k * x) * raggio,
            y0 + math.sin(k * x) * raggio
        ) for x in range(0, punti_cerchio + 1)]


def spicchi_cerchio(x0, y0, spicchi, raggio):
    if spicchi > 1:
        angolo_spicchio = 2 * math.pi / spicchi
        return [[
            (
                x0,
                y0
            ), (
                x0 + math.cos(angolo_spicchio * x) * raggio,
                y0 + math.sin(angolo_spicchio * x) * raggio
            )] for x in range(0, spicchi)]
    else:
        return []


def plot_diametri_shp(dati, destinazione):
    for filename in dati.keys():
        segmenti = shapefile.Writer(shapefile.POLYGON)
        segmenti.autoBalance = 1  # ensures gemoetry and attributes match
        segmenti.field("ID", "N")
        segmenti.field("LABEL", "C", 30)
        segmenti.field("VALORE", "F", decimal=5)
        for i, punto in enumerate(dati[filename]):
            label = punto['ID']
            x = punto['X']
            y = punto['Y']
            raggio = punto['D']
            valore = punto['V']
            punti = [coordinate_cerchio(x, y, 1, raggio)]
            segmenti.poly(parts=punti, shapeType=shapefile.POLYGON)
            segmenti.record(i, label, valore)

        directory_spicchi = os.path.join(destinazione, filename)
        if not os.path.exists(directory_spicchi):
            os.makedirs(directory_spicchi)
        segmenti.save(os.path.join(directory_spicchi, f'cerchi_{filename}.shp'))
        shutil.copy('proiezione.prj',
                    os.path.join(directory_spicchi, f'cerchi_{filename}.prj'))


def plot_diametri_dxf(dati, destinazione, diametro_iniziale):
    for filename in dati.keys():
        directory_dxf = os.path.join(destinazione, filename)
        if not os.path.exists(directory_dxf):
            os.makedirs(directory_dxf)

        dwg = ezdxf.new('AC1015')

        msp = dwg.modelspace()
        dwg.layers.new(name='TEXTLAYER', dxfattribs={'color': 7})
        dwg.layers.new(name='BORDERS', dxfattribs={'color': 7})
        livelli_creati = []
        for i, punto in enumerate(dati[filename]):
            label = punto['ID']
            x = punto['X']
            y = punto['Y']
            raggio = punto['D']
            punti = coordinate_cerchio(x, y, 1, raggio)
            colore = int(raggio - diametro_iniziale + 1)
            livello = f'CLASSE_{colore}'

            if livello not in livelli_creati:
                dwg.layers.new(name=livello, dxfattribs={'color': 7})
                livelli_creati.append(livello)

            msp.add_polyline2d(punti, dxfattribs={'layer': 'BORDERS'})

            hatch = msp.add_hatch(color=7, dxfattribs={'layer': livello})
            with hatch.edit_boundary() as boundary:
                boundary.add_polyline_path(punti, is_closed=1)
            msp.add_polyline2d(punti, dxfattribs={'layer': livello})

            msp.add_text(label, dxfattribs={'style': 'custom', 'height': 6, 'layer': "TEXTLAYER"}) \
                .set_pos((x + raggio + 2, y - raggio - 2), align='LEFT')

        dwg.saveas(os.path.join(directory_dxf, f'cerchi_{filename}.dxf'))


def plot_spicchi_shp(nome_foglio_di_calcolo, destinazione, label, layout, dati, raggio):
    spicchi = shapefile.Writer(shapefile.POLYLINE)
    spicchi.autoBalance = 1  # ensures gemoetry and attributes match
    spicchi.field("ID", "N")
    spicchi.field("LABEL", "C", 30)
    spicchi.field("PART", "C", 50)

    segmenti = shapefile.Writer(shapefile.POLYGON)
    segmenti.autoBalance = 1  # ensures gemoetry and attributes match
    segmenti.field("ID", "N")
    segmenti.field("LABEL", "C", 30)
    segmenti.field("ELEMENTO", "C", 50)

    filename = label.split('_')[1]
    elemento = label.split('_')[0]
    elementi = dati["raggruppamenti"][elemento]["elementi"]

    for i, punto in enumerate(layout.keys()):
        x = layout[punto]['X']
        y = layout[punto]['Y']
        num_spicchi = len(layout[punto]['SPICCHI'])

        punti = [coordinate_cerchio(x, y, num_spicchi, raggio)]
        spicchi.poly(parts=punti, shapeType=shapefile.POLYLINE)
        spicchi.record(i * 2, punto, 'CERCHIO')

        punti = spicchi_cerchio(x, y, num_spicchi, raggio)
        spicchi.poly(parts=punti, shapeType=shapefile.POLYLINE)
        spicchi.record(i * 2 + 1, punto, 'SPICCHI')

        for j, spicchio in enumerate(layout[punto]['SPICCHI']):
            if spicchio:
                punti = [coordinate_spicchio(x, y, num_spicchi, j, raggio)]
                segmenti.poly(parts=punti, shapeType=shapefile.POLYGON)
                segmenti.record(i * num_spicchi + j, punto, dati['colonne'][elementi[j]])

    directory_spicchi = os.path.join(destinazione, nome_foglio_di_calcolo)
    if not os.path.exists(directory_spicchi):
        os.makedirs(directory_spicchi)
    filename_spicchi = label.split('_')[1]
    spicchi.save(os.path.join(directory_spicchi, filename_spicchi, 'linee_{}.shp'.format(filename_spicchi)))
    shutil.copy('proiezione.prj',
                os.path.join(directory_spicchi, filename_spicchi, 'linee_{}.prj'.format(filename_spicchi)))

    directory = os.path.join(destinazione, nome_foglio_di_calcolo)
    if not os.path.exists(directory):
        os.makedirs(directory)

    segmenti.save(os.path.join(directory, filename, 'segmenti_{}.shp'.format(filename)))
    shutil.copy('proiezione.prj', os.path.join(directory, filename, 'segmenti_{}.prj'.format(filename)))


def plot_spicchi_dxf(nome_foglio_di_calcolo, destinazione, label, layout, dati, raggio):
    directory_dxf = os.path.join(destinazione, nome_foglio_di_calcolo)
    if not os.path.exists(directory_dxf):
        os.makedirs(directory_dxf)

    filename = os.path.join(directory_dxf, '{}.dxf'.format(label.split('_')[1]))

    dwg = ezdxf.new('AC1015')
    # print('available line types:')
    # for linetype in dwg.linetypes:
    #     print('{}: {}'.format(linetype.dxf.name, linetype.dxf.description))

    # available line types:
    # ByBlock:
    # ByLayer:
    # Continuous: Solid line
    # CENTER: Center ____ _ ____ _ ____ _ ____ _ ____ _ ____
    # DASHED: Dashed __ __ __ __ __ __ __ __ __ __ __ __ __ _
    # PHANTOM: Phantom ______  __  __  ______  __  __  ______
    # HIDDEN: Hidden __ __ __ __ __ __ __ __ __ __ __ __ __ __

    msp = dwg.modelspace()
    dwg.layers.new(name='TEXTLAYER', dxfattribs={'color': 0})
    dwg.layers.new(name='BORDERS', dxfattribs={'color': 0})

    elemento = label.split('_')[0]
    elementi = dati["raggruppamenti"][elemento]["elementi"]
    livelli_creati = {}

    for i, punto in enumerate(layout.keys()):
        x = layout[punto]['X']
        y = layout[punto]['Y']
        num_spicchi = len(layout[punto]['SPICCHI'])
        for j, spicchio in enumerate(layout[punto]['SPICCHI']):
            if spicchio:
                livello = dati['colonne'][elementi[j]].strip().replace('-', ' ').replace(',', '')

                if livello not in livelli_creati.keys():
                    colore = len(livelli_creati) + 1
                    dwg.layers.new(name=livello, dxfattribs={'color': colore})
                    livelli_creati[livello] = colore
                else:
                    colore = livelli_creati[livello]
                punti_spicchio = coordinate_spicchio(x, y, num_spicchi, j, raggio)
                hatch = msp.add_hatch(color=colore, dxfattribs={'layer': livello})
                with hatch.edit_boundary() as boundary:
                    boundary.add_polyline_path(punti_spicchio, is_closed=1)
                msp.add_polyline2d(punti_spicchio, dxfattribs={'layer': livello})

        punti = coordinate_cerchio(x, y, num_spicchi, raggio)

        msp.add_polyline2d(punti, dxfattribs={'layer': 'BORDERS'})

        segmenti = spicchi_cerchio(x, y, num_spicchi, raggio)
        for segmento in segmenti:
            msp.add_line(*segmento, dxfattribs={'layer': 'BORDERS'})

        msp.add_text(punto, dxfattribs={'style': 'custom', 'height': 6, 'layer': "TEXTLAYER"}) \
            .set_pos((x + raggio + 2, y - raggio - 2), align='LEFT')

    dwg.saveas(filename)

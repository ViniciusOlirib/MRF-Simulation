/*--------------------------------*- C++ -*----------------------------------*\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2012                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    location    "0";
    object      k;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -2 0 0 0 0];

internalField   uniform 0.08;

boundaryField
{
    #includeEtc "caseDicts/setConstraintTypes"

    inlet
    {
        type            inletOutlet; // Mudado de fixedValue para estabilidade de sucção
        inletValue      $internalField;
        value           $internalField;
    }

    outlet
    {
        type            inletOutlet;
        inletValue      $internalField;
        value           $internalField;
    }

    walls
    {
        type            zeroGradient; // CORRIGIDO: Removido fixedValue de parede sem lei de parede
    }

    propellerTip
    {
        type            kqRWallFunction; // Perfeito, mantenha assim
        value           $internalField;
    }
}


// ************************************************************************* //
